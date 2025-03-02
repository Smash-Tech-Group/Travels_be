import json, sys
from uuid import uuid4
from api.utils.files import delete_file
from api.utils import mime_types
from api.v1.services.tools.pdf_summarizer import pdf_summary_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

pdf_file_urls = payload.get('pdf_file_urls')
detail_level = payload.get('detail_level')
batch = payload.get('batch')

number_of_files_to_process = len(pdf_file_urls)
progress_per_file = round(95 / number_of_files_to_process)

summarized_pdf_list = []
final_data = {}

try:
    for id, url in enumerate(pdf_file_urls):
        if not batch:
            save_and_print_job_progress(db, job, 10, f'Downloading and opening PDF file from {url}')
        pdf_file_path = minio_service.download_file_from_minio(url)

        # Extract text from the PDF
        if not batch:
            save_and_print_job_progress(db, job, 30, 'Extracting data from uploaded PDF')
        pdf_data = pdf_summary_service.extract_pdf_data(pdf_file_path)

        # Split the text into chunks
        if not batch:
            save_and_print_job_progress(db, job, 40, 'Breaking PDF text into chunks for processing')
        chunks = pdf_summary_service.split_text_into_chunks(pdf_data.get('text'))

        # Summarize each chunk
        if not batch:
            save_and_print_job_progress(db, job, 50, 'Generating summary for PDF chunks')
        summaries = []
        for chunk in chunks:
            summary = pdf_summary_service.summarize_text(chunk, detail_level=detail_level)
            summaries.append(summary)

        # Combine the summaries
        if not batch:
            save_and_print_job_progress(db, job, 60, 'Generating final summary for PDF')
        final_summary = "\n".join(summaries)

        if not batch:
            save_and_print_job_progress(db, job, 70, 'Making calculations')
        # Calculate time saved
        time_saved = pdf_summary_service.get_reading_time(pdf_data.get('text'))- pdf_summary_service.get_reading_time(final_summary)
        final_time_saved = time_saved if time_saved > 0 else 0

        # Calculate summary word count
        summary_word_count = len(final_summary.split())
        
        # Calculate summary read time
        summary_read_time = pdf_summary_service.get_reading_time(summary)
        estimated_summary_read_time = f'{summary_read_time} minute' if summary_read_time == 1 else f'{summary_read_time} minutes'

        # Save summary to PDF
        if not batch:
            save_and_print_job_progress(db, job, 75, 'Saving summary to pdf')
        summary_pdf_file = pdf_summary_service.save_summary_to_pdf(text=final_summary)

        if not batch:
            save_and_print_job_progress(db, job, 85, 'Generating summary PDF preview and download link')
        preview_url, download_url = minio_service.upload_to_minio(
            folder_name='pdf-summarizer',
            source_file=summary_pdf_file,
            destination_file=f"pdfsum-{str(uuid4().hex)}.pdf",
            content_type=mime_types.APPLICATION_PDF,
        )

        if not batch:
            save_and_print_job_progress(db, job, 90, 'Generating result and performing final cleanup')

        # Remove text data from the pdf_data dictionary
        pdf_data.pop('text')
        delete_file(summary_pdf_file)

        data = {
            **pdf_data,
            'summary': final_summary,
            'summary_word_count': summary_word_count,
            'summary_read_time': estimated_summary_read_time,
            'time_saved': f'{final_time_saved} minute' if final_time_saved == 1 else f'{final_time_saved} minutes',
            "preview_url": preview_url,
            "download_url": download_url,
        }
        
        if not batch:
            save_and_print_job_progress(db, job, 95)
            
        if batch:
            summarized_pdf_list.append(data)

            save_and_print_job_progress(
                db, 
                job, 
                progress = (id+1) * progress_per_file, 
                progress_info = f'PDF {id+1} of {number_of_files_to_process} processed'
            )
        
    final_data = {'pdfs': summarized_pdf_list}
    
    print(json.dumps(final_data if batch else data))

except Exception as e:
    raise e
    
finally:
    delete_file(pdf_file_path)
