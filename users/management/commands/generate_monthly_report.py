import csv
import os
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.conf import settings
from django.db import models
from users.models import Farmer, MonthlyFarmerReport, User, Block

class Command(BaseCommand):
    help = "Generate a monthly farmer addition report, store in DB, and export to CSV."

    def handle(self, *args, **kwargs):
        today = now().date()
        current_month = today.month
        current_year = today.year

        self.stdout.write(f"🔹 Generating Monthly Report for {current_month}/{current_year}...")

        # Ensure the reports directory exists
        reports_dir = os.path.join(settings.BASE_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # CSV File Path
        csv_filename = f"monthly_report_{current_year}_{current_month}.csv"
        csv_filepath = os.path.join(reports_dir, csv_filename)

        # Get farmer count grouped by surveyor and block in a single query
        farmer_counts = Farmer.objects.filter(
            created_at__month=current_month, created_at__year=current_year
        ).values("added_by", "block").annotate(farmer_count=models.Count("id"))

        # Fetch users and blocks in a single query (Avoids looping DB calls)
        user_map = {user.id: user for user in User.objects.filter(id__in=[data["added_by"] for data in farmer_counts])}
        block_map = {block.id: block for block in Block.objects.filter(id__in=[data["block"] for data in farmer_counts])}

        # Prepare list for bulk update
        report_objects = []
        
        # Open CSV file and write data
        with open(csv_filepath, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Surveyor Name", "Block Name", "Month", "Year", "Farmers Added"])

            for data in farmer_counts:
                surveyor = user_map[data["added_by"]]
                block = block_map[data["block"]]
                count = data["farmer_count"]

                # Prepare MonthlyFarmerReport object for bulk update
                report_objects.append(MonthlyFarmerReport(
                    surveyor=surveyor,
                    block=block,
                    month=current_month,
                    year=current_year,
                    count=count
                ))

                # Write to CSV
                writer.writerow([surveyor.username, block.name, current_month, current_year, count])

                self.stdout.write(f"✅ Report for {surveyor.username} - {block.name}: {count} farmers.")

        # Bulk update all records in one go (Avoids update loop)
        MonthlyFarmerReport.objects.bulk_create(report_objects, ignore_conflicts=True)

        self.stdout.write(f"📂 CSV Report Saved: {csv_filepath}")
