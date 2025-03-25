import redis
from celery import shared_task
from django.utils.timezone import localtime,now
from users.models import Farmer, DailyFarmerCount, MonthlyFarmerReport
from django.contrib.auth import get_user_model
from django.db.models import Sum

User = get_user_model()
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

@shared_task
def store_and_reset_farmer_counts():
    """ Store daily farmer counts in DB and reset Redis at midnight. """
    today = localtime().date()
    surveyor_ids = Farmer.objects.values_list('added_by_id', flat=True).distinct()

    for surveyor_id in surveyor_ids:
        if not surveyor_id:
            continue  # Skip if no valid surveyor_id

        surveyor = User.objects.filter(id=surveyor_id, role='surveyor').first()
        if not surveyor or not surveyor.block:
            continue  # Skip if surveyor has no block assigned

        block = surveyor.block

        # 🔹 Redis Keys
        surveyor_key = f"surveyor:{surveyor.id}:daily_farmer_count"
        block_key = f"block:{block.id}:daily_farmer_count"

        # 🔹 Fetch Counts Safely
        my_count = int(redis_client.get(surveyor_key) or 0)
        block_count = int(redis_client.get(block_key) or 0)

        # ✅ Store only if the surveyor added farmers
        if my_count > 0:
            DailyFarmerCount.objects.create(
                surveyor=surveyor,
                block=block,
                date=today,
                count=my_count
            )

        # ✅ Reset Redis Counts (Deletes the key instead of setting it to 0)
        redis_client.delete(surveyor_key)
        redis_client.delete(block_key)

    return "✅ Farmer counts stored in DB & Redis reset successfully."




# @shared_task
# def generate_monthly_farmer_report():
#     """ Aggregate daily counts & store monthly totals """
    
#     today = now().date()
#     prev_month = today.month - 1 if today.month > 1 else 12
#     prev_year = today.year if today.month > 1 else today.year - 1

#     # Get all surveyors who added farmers
#     surveyor_ids = DailyFarmerCount.objects.filter(
#         date__month=prev_month,
#         date__year=prev_year
#     ).values_list('surveyor_id', flat=True).distinct()

#     for surveyor_id in surveyor_ids:
#         if not surveyor_id:
#             continue  # Skip invalid IDs

#         surveyor = User.objects.filter(id=surveyor_id, role='surveyor').first()
#         if not surveyor or not surveyor.block:
#             continue  # Skip surveyors without a block

#         block = surveyor.block

#         # Calculate total farmers added in the previous month
#         total_farmers = DailyFarmerCount.objects.filter(
#             surveyor=surveyor,
#             date__month=prev_month,
#             date__year=prev_year
#         ).aggregate(Sum('count'))['count'] or 0

#         # Store in MonthlyFarmerReport
#         MonthlyFarmerReport.objects.update_or_create(
#             surveyor=surveyor,
#             block=block,
#             month=prev_month,
#             year=prev_year,
#             defaults={'count': total_farmers}
#         )

#     return f"✅ Monthly report generated for {prev_month}/{prev_year}."
