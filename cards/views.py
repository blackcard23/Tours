import random
from datetime import timedelta, datetime

from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from avtorizate.models import VerificationCode
from tours.models import Booking
from .models import Card, Category, Transaction
from .serializers import CardSerializer, CategorySerializer, TransactionSerializer, PaymentSerializer


class CardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cards = Card.objects.filter(user=request.user)
        serializer = CardSerializer(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            card_num = ''.join(str(random.randint(0, 9)) for _ in range(16))

            current_date = datetime.now()
            expiry_date = (current_date + timedelta(days=10*365)).strftime('%m/%y')

            card_name = request.data.get('card_name', 'Unnamed Card')

            card = Card.objects.create(
                user=request.user,
                card_num=card_num,
                mm_yy=expiry_date,
                balance=99999,
                card_name=card_name
            )

            serializer = CardSerializer(card)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(from_card__user=self.request.user)
        card_ids = self.request.query_params.getlist('card', None)
        period_start = self.request.query_params.get('start', None)
        period_end = self.request.query_params.get('end', None)
        value_type = self.request.query_params.get('type', None)

        if card_ids:
            queryset = queryset.filter(from_card__id__in=card_ids)
        if period_start and period_end:
            queryset = queryset.filter(datetime__range=[period_start, period_end])
        if value_type == 'income':
            queryset = queryset.filter(value__gt=0)
        elif value_type == 'expense':
            queryset = queryset.filter(value__lt=0)

        return queryset

    def perform_create(self, serializer):
        from_card = get_object_or_404(Card, id=self.request.data.get('from_card'), user=self.request.user)
        to_card = get_object_or_404(Card, id=self.request.data.get('to_card'), user=self.request.user)
        serializer.save(from_card=from_card, to_card=to_card)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def transfer(self, request):
        from_card = get_object_or_404(Card, id=request.data.get('from_card'), user=request.user)
        to_card = get_object_or_404(Card, id=request.data.get('to_card'), user=request.user)
        value = float(request.data.get('value'))
        category_id = request.data.get('category')

        if from_card.balance < value:
            return Response({'error': 'Недостаточно средств на карте'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            from_card.balance -= value
            from_card.save()
            to_card.balance += value
            to_card.save()

            transaction_instance = Transaction.objects.create(
                value=-value,
                from_card=from_card,
                to_card=to_card,
                category_id=category_id
            )

        return Response({'status': 'перевод успешен', 'transaction_id': transaction_instance.id}, status=200)





class PaymentView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def post(self, request):
        booking = get_object_or_404(Booking, id=request.data.get('booking_id'), user=request.user)
        card = get_object_or_404(Card, id=request.data.get('card_id'), user=request.user)

        if booking.is_paid:
            return Response({"error": "Оплата уже была произведена."}, status=status.HTTP_400_BAD_REQUEST)

        if card.balance < booking.total_price:
            return Response({"error": "Недостаточно средств."}, status=status.HTTP_400_BAD_REQUEST)

        tour_card = get_object_or_404(Card, card_num="7777777777777777")

        with transaction.atomic():
            card.balance -= booking.total_price
            card.save()

            tour_card.balance += booking.total_price
            tour_card.save()

            Transaction.objects.create(
                value=-booking.total_price,
                from_card=card,
                to_card=tour_card,
                category_id=1
            )

            booking.is_paid = True
            booking.save()

            booking_details = "\n".join([
                f"<strong>Тур:</strong> {booking.tour.name}<br>",
                f"<strong>Дата:</strong> {booking.tour.date}<br>",
                f"<strong>Общее количество людей:</strong> {booking.people_count}<br>",
                f"<strong>Общая стоимость:</strong> {booking.total_price:.2f} $"
            ])

            message = f"""
<html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; background-color: #f5f5f5; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 20px auto; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); background-color: #fff;">
            <!-- Header -->
            <header style="background: linear-gradient(45deg, #4CAF50, #6BBE92); color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">Бронирование подтверждено!</h1>
                <p style="margin: 5px 0; font-size: 16px;">Спасибо за выбор наших услуг!</p>
            </header>

            <!-- Body -->
            <main style="padding: 20px;">
                <p>Здравствуйте,</p>
                <p>С радостью сообщаем, что ваша оплата на сумму <strong>${booking.total_price:.2f}</strong> была успешно обработана.</p>
                <p style="margin-top: 20px;">Детали вашего бронирования:</p>
                <div style="border: 1px solid #eee; background-color: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    {booking_details}
                </div>
                <p>Если у вас возникли вопросы, мы всегда рады помочь. Обратитесь в нашу службу поддержки в любое время.</p>
            </main>

            <!-- Advertisement -->
            <section style="background: #fafafa; padding: 20px; border-top: 1px solid #ddd;">
                <h3 style="font-size: 18px; color: #4CAF50; text-align: center;">Смотрите и управляйте своими турами в Telegram!</h3>
                <p style="text-align: center; color: #666;">Теперь вы можете использовать нашего удобного Telegram-бота для просмотра своих бронирований и новых предложений.</p>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="https://t.me/tour2323_bot" style="text-decoration: none; padding: 10px 20px; background: #4CAF50; color: white; border-radius: 5px; font-size: 16px;">Перейти в Telegram</a>
                </div>
                <p style="text-align: center; color: #666;">И не забудьте подписаться на нас в Instagram!</p>
                <div style="text-align: center; margin-top: 10px;">
                    <a href="https://instagram.com/touragency_23" style="text-decoration: none;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" alt="Instagram" style="width: 40px; height: 40px; margin: 0 5px;">
                    </a>
                </div>
            </section>

            <!-- Footer -->
            <footer style="background: #4CAF50; color: white; text-align: center; padding: 10px;">
                <p style="margin: 0; font-size: 14px;">С уважением, ваша команда поддержки</p>
                <p style="margin: 0; font-size: 12px;">Все права защищены © 2024</p>
            </footer>
        </div>
    </body>
</html>
"""



            # Отправляем сообщение на email пользователя
            send_mail(
                subject='Успешная оплата',
                message='Ваш почтовый клиент не поддерживает HTML.',
                html_message=message,
                from_email='agzamovsaid14@gmail.com',
                recipient_list=[request.user.email],
                fail_silently=False,
            )

        return Response({"status": "Оплата прошла успешно"}, status=status.HTTP_200_OK)




