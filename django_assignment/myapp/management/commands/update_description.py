# import os
# import psycopg2
# import httpx
# import json
# from django.core.management.base import BaseCommand
# from dotenv import load_dotenv

# load_dotenv()

# SOURCE_DB = {
#     'dbname': os.getenv('DJANGO_DATABASE', 'django_database'),
#     'user': os.getenv('DB_USER', 'postgres'),
#     'password': os.getenv('PASSWORD', 'p@stgress'),
#     'host': os.getenv('HOST', 'localhost'),
#     'port': os.getenv('PORT', '5433')
# }

# class Command(BaseCommand):
#     help = 'Generate descriptions for properties using gemma2:2b and update the description column.'

#     def handle(self, *args, **kwargs):
#         conn = psycopg2.connect(**SOURCE_DB)
#         cur = conn.cursor()
#         ollama_url = "http://localhost:11434/api/generate"
#         print(f"Ollama URL: {ollama_url}")
#         client = httpx.Client()

#         try:
#             cur.execute("SELECT property_id, title, price, room_type, rating FROM myapp_property")
#             properties = cur.fetchall()

#             for property in properties:
#                 property_id, title, price, room_type, rating = property
#                 prompt = f"Generate a concise 3-line description for a property with the following details:\nTitle: {title}\nPrice: ${price}\nRoom Type: {room_type}\nRating: {rating}/5"

#                 try:
#                     response = client.post(
#                         ollama_url,
#                         json={"model": "gemma2:2b", "prompt": prompt},
#                         timeout=30
#                     )
#                     response.raise_for_status()

#                     # Handle streaming response
#                     full_response = ""
#                     for line in response.iter_lines():
#                         if line:
#                             try:
#                                 json_response = json.loads(line)
#                                 if 'response' in json_response:
#                                     full_response += json_response['response']
#                             except json.JSONDecodeError:
#                                 continue  # Skip lines that can't be parsed as JSON

#                     generated_text = full_response.strip()
#                     self.stdout.write(self.style.SUCCESS(f'Generated description for property: {title}'))
#                     self.stdout.write(self.style.SUCCESS(f'Description: {generated_text}'))

#                     update_query = "UPDATE myapp_property SET description = %s WHERE property_id = %s"
#                     cur.execute(update_query, (generated_text[:255], property_id))
#                     conn.commit()

#                     self.stdout.write(self.style.SUCCESS(f'Updated description for property: {title}'))
#                 except httpx.HTTPStatusError as http_err:
#                     self.stdout.write(self.style.ERROR(f'HTTP error occurred: {http_err}'))
#                 except httpx.RequestError as req_err:
#                     self.stdout.write(self.style.ERROR(f'Request error occurred: {req_err}'))
#                 except Exception as e:
#                     self.stdout.write(self.style.ERROR(f'An error occurred while processing property {title}: {str(e)}'))

#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
#         finally:
#             cur.close()
#             conn.close()




##New
import os
import psycopg2
import httpx
import json
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
    help = 'Generate descriptions and summaries for properties using gemma2:2b and update the database.'

    def handle(self, *args, **kwargs):
        ollama_url = "http://localhost:11434/api/generate"
        print(f"Ollama URL: {ollama_url}")
        client = httpx.Client()

        properties = Property.objects.all()

        for property in properties:
            try:
                # Generate description
                description_prompt = f"Generate a concise 3-line description for a property with the following details:\nTitle: {property.title}\nPrice: {property.price}\nRoom Type: {property.room_type}\nRating: {property.rating}"
                description = self.generate_ollama_response(client, ollama_url, description_prompt)
                
                # Update description
                property.description = description[:255]  # Truncate to 255 characters
                property.save()
                self.stdout.write(self.style.SUCCESS(f'Updated description for property: {property.title}'))

                # Generate summary
                summary_prompt = f"Generate a comprehensive summary for a property with the following details:\nTitle: {property.title}\nDescription: {property.description}\nPrice: {property.price}\nRoom Type: {property.room_type}\nRating: {property.rating}\nAmenities: {', '.join([a.name for a in property.amenities.all()])}\nLocations: {', '.join([l.name for l in property.locations.all()])}"
                summary = self.generate_ollama_response(client, ollama_url, summary_prompt)

                # Save or update summary
                property_summary, created = PropertySummary.objects.update_or_create(
                    property=property,
                    defaults={'summary': summary}
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
                        continue  # Skip lines that can't be parsed as JSON

            return full_response.strip()

        except httpx.HTTPStatusError as http_err:
            self.stdout.write(self.style.ERROR(f'HTTP error occurred: {http_err}'))
        except httpx.RequestError as req_err:
            self.stdout.write(self.style.ERROR(f'Request error occurred: {req_err}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))

        return ""  # Return empty string if there was an error