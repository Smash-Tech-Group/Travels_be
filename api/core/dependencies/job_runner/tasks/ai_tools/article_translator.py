import json, sys, os, io
from uuid import uuid4

from api.db.database import get_db
from api.v1.services.job import tifi_job_service
from api.utils.files import delete_file
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils.pdf_builder import PDFBuilder
from api.utils import mime_types
from api.v1.services.tools.article_translator import article_translator_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

article = payload.get('article')
languages = payload.get('languages')
names = payload.get('names')

number_to_process = len(languages)
progress_per_article = round(75 / number_to_process)

articles = []

# Initialize pdf builder
pdf_buffer = io.BytesIO()
pdf_builder = PDFBuilder(pdf_buffer)

try:
    for i in range(len(languages)):
        translated_article = article_translator_service.generate_translated_article(
            article=article,
            language=languages[i],
            name=names[i]
        )

        # Build PDF file
        pdf_builder.add_section(title=languages[i].capitalize(), text=translated_article)

        articles.append({
            'language': languages[i],
            'translated_article': translated_article
        })

        save_and_print_job_progress(
            db, 
            job, 
            progress = (i+1) * progress_per_article, 
            progress_info = f'{languages[i]} article generated. {number_to_process-(i+1)} remaining'
        )
    
    save_and_print_job_progress(db, job, 80, 'Building PDF file')
    pdf_builder.build()

    save_and_print_job_progress(db, job, 85, 'Saving PDF file')
    # Save the PDF content to a file
    pdf_buffer.seek(0)
    pdf_file = os.path.join(settings.TEMP_DIR, f"artclgen-{uuid4().hex}.pdf")
    with open(pdf_file, "wb") as f:
        f.write(pdf_buffer.read())

    pdf_buffer.close()

    save_and_print_job_progress(db, job, 90, 'Uploading PDF file for storage')
    save_url, download_url = minio_service.upload_to_minio(
        folder_name="article-translator-generator",
        source_file=pdf_file,
        destination_file=f"artclgen-{str(uuid4().hex)}.pdf",
        content_type=mime_types.APPLICATION_PDF,
    )

    save_and_print_job_progress(db, job, 95, 'Cleaning up')
    delete_file(pdf_file)

    save_and_print_job_progress(db, job, 97, 'Generating result')

    result = {
        'articles': articles,
        'pdf': {
            'preview_url': save_url,
            'download_url': download_url
        }
    }
    print(json.dumps(result))

except Exception as e:
    raise e
