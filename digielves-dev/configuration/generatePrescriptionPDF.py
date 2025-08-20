from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fpdf import FPDF
import json
import xml.etree.ElementTree as ET
from digielves_setup.models import DoctorPersonalDetails, DoctorConsultation, DoctorPrescriptions
from doctor.seriallizers.consultation import ShowDoctorConsultationSerializer, DoctorPrescriptionsSerializer
from configuration import settings
import shutil 

def generate_prescription(prescription_data, consultation_id, file_name="output_1234.pdf"):

    print(consultation_id)
    doctor_details = DoctorConsultation.objects.get(id=consultation_id)
    userSerialData = ShowDoctorConsultationSerializer(doctor_details)
    data = userSerialData.data
    medications = DoctorPrescriptions.objects.filter(consultation_id=consultation_id)
    userSerialData = DoctorPrescriptionsSerializer(medications, many=True)
    medications = userSerialData.data
    print(medications)

    # Fetch doctor details directly from the instance
    doctor = doctor_details.doctor_id
    doctor_slot = doctor_details.doctor_slot

    # Extract necessary information
    name = f"{doctor.firstname} {doctor.lastname}"
    speciality = f"{doctor_slot.doctor.speciality} | Reg No {doctor_slot.doctor.license_no}"
    contact = doctor.phone_no
    mail = doctor.email
    patient = data['consultation_for']['full_name']
    gender = data['consultation_for']['gender']
    age = data['consultation_for']['age']
    date = data['appointment_date']
    slot = data['doctor_slot']['slots']
    mode = data['doctor_slot']['meeting_mode']
    reason = data['reason_for_consultation']
    note = data['dignosis']  # Corrected variable name
    advice = data['advice']
    reschedule_date = data['reschedule_by']
    followup_date = data['next_appointment']

    # Define custom page size with increased width and height
    custom_page_width = 692  # You can adjust this value as needed
    custom_page_height = 912  # You can adjust this value as needed
    custom_page_size = (custom_page_width, custom_page_height)

    # Create canvas with custom page size
    c = canvas.Canvas(file_name, pagesize=custom_page_size)

    # Add doctor logo on the left side
    doctor_logo_path = r"logo.png"
    c.drawImage(doctor_logo_path, 50, custom_page_height - 100, width=100, height=100)

    # Add doctor details at the top-right corner
    c.setFont("Helvetica", 10)  # Smaller font size
    doctor_details_lines = [
        f"{name}",
        f"{speciality}",
        f"Contact: {contact}",
        f"Email: {mail}"
    ]
    doctor_y = custom_page_height - 50
    for line in doctor_details_lines:
        c.drawRightString(custom_page_width - 50, doctor_y, line)
        doctor_y -= 12  # Decreased line spacing

    # Add patient details
    c.setFont("Helvetica-Bold", 9)  # Smaller font size
    c.drawString(50, custom_page_height - 120, "PATIENT DETAILS:")
    c.setFont("Helvetica", 8) 
    patient_y = custom_page_height - 140
    
    
    
    patient_details_columns = [
        f"Patient Name: {patient}",
        f"Gender: {gender}",
        f"Contact: {contact}",
        # f"Mail: {mail}",
        f"Age: {age}",
        f"Date: {date}",
        f"Slots: {slot}",
        f"Mode: {mode}",
        f"Notes: {note}",
        # f"Advice Given: {advice}",
        f"Reason for Consultation: {reason}",
        f"Reschedule Date: {reschedule_date}",
        # f"Follow-up Date: {followup_date}",
    ]


    column_mapping = {
    "Medication Name": "medicine_name",
    "Strength": "strength",
    "Dosage": "doses",
    "Units": "units",
    "Frequency": "frequency",
    "Method": "method",
    "Duration": "duration",
    "Notes": "notes"
    }



    for i in range(len(patient_details_columns)):
        c.drawString(70, patient_y, patient_details_columns[i])  # Align all columns to the left
        patient_y -= 15  # Decreased line spacing



        

    # Draw horizontal line after patient details
    patient_line_y = custom_page_height - 120
    c.line(50, patient_line_y - 5, 645, patient_line_y - 5)

    # Add dignosis notes
    c.setFont("Helvetica-Bold", 9)  # Smaller font size
    c.drawString(50, patient_y - 25, "DIAGNOSIS NOTES:")  # Adjusted position
    c.setFont("Helvetica", 8)  # Smaller font size
    dignosis_y = patient_y - 45  # Adjusted position
    for line in note.split('\n'):
        c.drawString(70, dignosis_y, line)
        dignosis_y -= 12  # Decreased line spacing

    # Draw horizontal line after diagnosis notes
    patient_line_y = custom_page_height - (custom_page_height - patient_y + 26)
    c.line(50, patient_line_y - 5, 645, patient_line_y - 5)  # Adjusted horizontal line position

    # Add medication table title
    c.setFont("Helvetica-Bold", 9)
    table_title_y = dignosis_y - 40  # Adjusted position
    c.drawString(50, table_title_y, "MEDICATION PRESCRIBED:")  # Adjusted position

    # Add table for medication data
    column_names = ["Medication Name", "Strength", "Dosage", "Units", "Frequency", "Method", "Duration", "Notes"]
    num_columns = len(column_names)
    
    # Calculate column widths dynamically based on content
    column_widths = [80, 40, 40, 60, 60, 60, 50, 100]  # Example widths, adjust as needed
    row_height = 15  # Decreased row height
    table_x = 50
    table_y = table_title_y - 30  # Adjusted position

    # Draw table headers
    for i, column_name in enumerate(column_names):
        column_widths[i] = max(column_widths[i], max([c.stringWidth(str(row.get(column_name, ""))) for row in medications]) + 10)
        c.rect(table_x + sum(column_widths[:i]), table_y, column_widths[i], row_height, stroke=1)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(table_x + sum(column_widths[:i]) + (column_widths[i] - c.stringWidth(column_name)) / 2, table_y + 3, column_name)  # Center align column names


    # Draw table data
    # Draw table data
    for row_index, row in enumerate(medications):
        for col_index, column_name in enumerate(column_names):
            # ...
            c.rect(table_x + sum(column_widths[:col_index]), table_y - (row_index + 1) * row_height, column_widths[col_index], row_height, stroke=1, fill=0)
            c.setFont("Helvetica", 7)  # Set font size for table data
            dict_key = column_mapping.get(column_name, column_name.lower().replace(" ", "_"))
            value = row.get(dict_key, "")
            # ...
            c.drawString(table_x + sum(column_widths[:col_index]) + 5, table_y - (row_index + 1) * row_height + 3, str(value))


    # Add advice given
    c.setFont("Helvetica-Bold", 9)  # Smaller font size
    c.drawString(50, table_y - (len(medications) + 2) * row_height - 25, "ADVICE GIVEN:")
    c.setFont("Helvetica", 8)  # Smaller font size
    advice_y = table_y - (len(medications) + 2) * row_height - 45
    for line in advice.split('\n'):
        c.drawString(70, advice_y, line)
        advice_y -= 12  # Decreased line spacing

    # Add Follow Up Date
    c.setFont("Helvetica-Bold", 9)  # Smaller font size
    c.drawString(50, advice_y - 25, "FOLLOW UP DATE:")
    c.setFont("Helvetica", 8)  # Smaller font size
    c.drawString(150, advice_y - 25, followup_date)

    c.save()
    # Save the PDF to the media folder
    pdf_name = settings.MEDIA_ROOT + '/consultation/prescription/Prescription_' + str(consultation_id) + '.pdf'
    shutil.move(file_name, pdf_name)  # Move the generated PDF to the media folder with the desired name

    return '/consultation/prescription/Prescription_'+ str(consultation_id)+'.pdf'

    



