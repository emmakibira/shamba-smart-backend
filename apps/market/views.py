from rest_framework.permissions import AllowAny
import io
import re
import logging
from datetime import date

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MarketPrice
from .serializers import MarketPriceSerializer
from utils.firebase_utils import FirebaseAuth

logger = logging.getLogger(__name__)


def _parse_pdf_bytes(pdf_bytes: bytes) -> list[dict]:
    """Extract rows from PDF. Requires pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if not row or len(row) < 2:
                    continue
                crop = (row[0] or "").strip()
                price_raw = (row[1] or "").strip()
                market = (row[2] or "").strip() if len(row) > 2 else "National"

                if not crop or not price_raw:
                    continue
                # Skip header rows
                if re.search(r'crop|zao|bei|price', crop, re.IGNORECASE):
                    continue

                price_clean = re.sub(r'[^\d.]', '', price_raw)
                if not price_clean:
                    continue
                try:
                    rows.append({
                        'crop_name': crop,
                        'price': float(price_clean),
                        'market': market or 'National',
                    })
                except ValueError:
                    continue
    return rows


class MarketPriceUploadView(APIView):
    """POST /api/market/upload-pdf/ — Admin/Officer uploads weekly price PDF."""
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({'error': 'Only PDF files are accepted.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rows = _parse_pdf_bytes(pdf_file.read())
        except ImportError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("PDF parse error")
            return Response({'error': f'PDF parsing failed: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        if not rows:
            return Response(
                {'error': 'No price data found. Check PDF format: Crop Name | Price (TSh) | Market Location'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = date.today()
        created = []
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return Response(
                {'error': 'Only admin users may upload market price data.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        for row in rows:
            obj, _ = MarketPrice.objects.update_or_create(
                crop_name=row['crop_name'],
                market=row['market'],
                date=today,
                defaults={'price': row['price'], 'uploaded_by': request.user},
            )
            created.append(obj)

        try:
            # Also keep a copy in Firestore for admin-maintained market data.
            FirebaseAuth.write_market_price_rows(
                [
                    {
                        'crop_name': r.crop_name,
                        'price': float(r.price),
                        'market': r.market,
                        'date': r.date.isoformat(),
                        'created_at': r.created_at.isoformat() if r.created_at else None,
                        'uploaded_by': request.user.email or request.user.username,
                    }
                    for r in created
                ],
                metadata={'source': 'backend_pdf_upload', 'uploaded_by': request.user.email or request.user.username},
            )
        except Exception:
            logger.warning('Failed to replicate market price rows to Firestore.')

        return Response({
            'message': f'Successfully imported {len(created)} price records.',
            'rows_imported': len(created),
        }, status=status.HTTP_201_CREATED)


class MarketPriceListView(generics.ListAPIView):
    """GET /api/market/prices/ — List latest market prices."""
    serializer_class = MarketPriceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = MarketPrice.objects.all()
        crop = self.request.query_params.get('crop')
        if crop:
            qs = qs.filter(crop_name__icontains=crop)
        return qs[:100]
