import os
import psycopg2
from datetime import datetime
import requests
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from django.conf import settings

load_dotenv()

# Database configurations from .env file
SOURCE_DB = {
    'dbname': os.getenv('SCRAPY_DATABASE', 'hotel_db'),
    'user': os.getenv('DB_USER') or 'postgres',
    'password': os.getenv('PASSWORD', 'p@stgress'),
    'host': os.getenv('HOST', 'localhost'),
    'port': os.getenv('PORT', '5433')
}

DEST_DB = {
    'dbname': os.getenv('DJANGO_DATABASE', 'django_database'),
    'user': os.getenv('DB_USER') or 'postgres',
    'password': os.getenv('PASSWORD', 'p@stgress'),
    'host': os.getenv('HOST', 'localhost'),
    'port': os.getenv('PORT', '5433')
}

# Update IMAGE_PATH to reflect the folder structure
IMAGE_PATH = "media/property_images/"

class Command(BaseCommand):
    help = 'Migrate data from the source database to the Django database.'

    def handle(self, *args, **kwargs):
        if not self.confirm_migration():
            self.stdout.write(self.style.ERROR('Migration aborted.'))
            return
        
        self.migrate_data()
        self.stdout.write(self.style.SUCCESS('Data successfully migrated.'))

    def confirm_migration(self):
        """Ask user for confirmation before proceeding with migration."""
        while True:
            confirmation = input("Are you sure you want to migrate data? (Yes/No): ").strip().lower()
            if confirmation in ('yes', 'no'):
                return confirmation == 'yes'
            self.stdout.write(self.style.ERROR("Invalid input. Please enter 'Yes' or 'No'."))

    def download_image(self, image_url, image_filename):
        """Download image from a URL and save it to the specified file path."""
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            os.makedirs(os.path.dirname(image_filename), exist_ok=True)
            with open(image_filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            self.stdout.write(self.style.SUCCESS(f"Downloaded image from {image_url} to {image_filename}"))
            return image_filename
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to download image from {image_url}: {e}"))
            return None

    def migrate_data(self):
        """Perform the data migration from source to destination database."""
        src_conn = None
        src_cursor = None
        dest_conn = None
        dest_cursor = None
        try:
            src_conn = psycopg2.connect(**SOURCE_DB)
            src_cursor = src_conn.cursor()
            dest_conn = psycopg2.connect(**DEST_DB)
            dest_cursor = dest_conn.cursor()

            src_cursor.execute("SELECT id, title, price, room_type, rating, location, latitude, longitude, image_url FROM hotels_data")
            rows = src_cursor.fetchall()

            for row in rows:
                id, title, price, room_type, rating, location, latitude, longitude, image_url = row
                current_time = datetime.now()

                image_filename = os.path.join(IMAGE_PATH, os.path.basename(image_url))
                downloaded_image_path = self.download_image(image_url, image_filename)

                relative_image_path = os.path.join("property_images", os.path.basename(image_url))

                dest_cursor.execute("""
                    INSERT INTO myapp_property (title, description, price, room_type, rating, create_date, update_date) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING property_id;
                    """, (title, "NULL", price, room_type, rating, current_time, current_time))

                property_id = dest_cursor.fetchone()[0]

                if downloaded_image_path:
                    dest_cursor.execute("""
                        INSERT INTO myapp_image (image, create_date, property_id, update_date) 
                        VALUES (%s, %s, %s, %s)
                        """, (relative_image_path, current_time, property_id, current_time))

                dest_cursor.execute("""
                    SELECT id FROM myapp_location WHERE name = %s AND type = %s AND longitude = %s AND latitude = %s
                    """, (location, "", longitude, latitude))
                location_id = dest_cursor.fetchone()

                if not location_id:
                    dest_cursor.execute("""
                        INSERT INTO myapp_location (name, type, longitude, latitude, create_date, update_date) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """, (location, "null", longitude, latitude, current_time, current_time))
                    location_id = dest_cursor.fetchone()[0]
                else:
                    location_id = location_id[0]

                dest_cursor.execute("""
                    INSERT INTO myapp_property_locations (property_id, location_id)
                    VALUES (%s, %s)
                    """, (property_id, location_id))

            dest_conn.commit()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
        finally:
            if src_cursor:
                src_cursor.close()
            if src_conn:
                src_conn.close()
            if dest_cursor:
                dest_cursor.close()
            if dest_conn:
                dest_conn.close()
