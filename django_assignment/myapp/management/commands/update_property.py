import os
import psycopg2
import httpx
import json
import re
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from myapp.models import Property, PropertySummary

load_dotenv()

SOURCE_DB = {
    'dbname': os.getenv('DJANGO_DATABASE', 'django_database'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('PASSWORD', 'p@stgress'),
    'host': os.getenv('HOST', 'localhost'),
    'port': os.getenv('PORT', '5433')
}

class Command(BaseCommand):
    help = 'Generate descriptions, titles, and summaries for properties using gemma2:2b and update the database.'

    def handle(self, *args, **kwargs):
        ollama_url = "http://localhost:11434/api/generate"
        print(f"Ollama URL: {ollama_url}")
        client = httpx.Client()

        properties = Property.objects.all()

        for property in properties:
            try:
                # Generate description
                description_prompt = (
                    f"Generate a description for a property with the following details. "
                    f"Do not include any special characters, emojis, or formatting:\n"
                    f"Title: {property.title}\n"
                    f"Price: {property.price}\n"
                    f"Room Type: {property.room_type}\n"
                    f"Rating: {property.rating}"
                )
                description = self.generate_ollama_response(client, ollama_url, description_prompt)
                property.description = self.clean_text(description)[:255]
                
                # Generate a new title
                title_prompt = (
                    f"Create a single unique and catchy title (max 60 characters) for this specific property. "
                    f"Do not include any special characters, emojis, or formatting:\n"
                    f"Description: {property.description}\n"
                    f"Price: {property.price}\n"
                    f"Rating: {property.rating}\n"
                    f"Room Type: {property.room_type}"
                )
                new_title = self.generate_ollama_response(client, ollama_url, title_prompt)
                property.title = self.clean_text(new_title)[:60]  # Changed to 60 characters as per the prompt
                
                property.save()
                self.stdout.write(self.style.SUCCESS(f'Updated description and title for property. New title: {property.title}'))

                # Generate summary
                summary_prompt = (
                    f"Generate a comprehensive summary as a single paragraph for a property with these details. "
                    f"Do not include any special characters, emojis, or formatting:\n"
                    f"Title: {property.title}\n"
                    f"Description: {property.description}\n"
                    f"Price: {property.price}\n"
                    f"Room Type: {property.room_type}\n"
                    f"Rating: {property.rating}\n"
                    f"Amenities: {', '.join([a.name for a in property.amenities.all()])}\n"
                    f"Locations: {', '.join([l.name for l in property.locations.all()])}"
                )
                summary = self.generate_ollama_response(client, ollama_url, summary_prompt)

                property_summary, created = PropertySummary.objects.update_or_create(
                    property=property,
                    defaults={'summary': self.clean_text(summary)}
                )
                self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} summary for property: {property.title}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred while processing property {property.title}: {str(e)}'))

    def generate_ollama_response(self, client, url, prompt):
        try:
            response = client.post(
                url,
                json={"model": "gemma2:2b", "prompt": prompt},
                timeout=30
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        if 'response' in json_response:
                            full_response += json_response['response']
                    except json.JSONDecodeError:
                        continue

            return full_response.strip()

        except httpx.HTTPStatusError as http_err:
            self.stdout.write(self.style.ERROR(f'HTTP error occurred: {http_err}'))
        except httpx.RequestError as req_err:
            self.stdout.write(self.style.ERROR(f'Request error occurred: {req_err}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))

        return ""

    def clean_text(self, text):
        clean = re.sub(r'[^\w\s$]', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()