from fpdf import FPDF
import json
import xml.etree.ElementTree as ET
from digielves_setup.models import DoctorPersonalDetails, DoctorConsultation
from doctor.seriallizers.consultation import ShowDoctorConsultationSerializer
from configuration import settings

def generate_prescription(prescriptionData,  consultation_id):
    # consultation_id = 4
    print("------------------------------------------------Prescription Data--------------------------------------------------")
    print(prescriptionData)
    # dr_name= 'Dr. James Toe',
    dr_qual = 'MBBS MS(General Surgery), M.ch Neurology | Reg No 421361',
    # dr_add = 'XYZ Hospital Jubilee Hills Hyderabad-500003 | Telangana, India',
    # dr_contact = '+ 91 0000 0000',
    patient_name='John Markson',
    gender='Male',
    age='36 yrs',
    # contact='+91 0000 0000',
    consult_type='Online',
    consulting_reason='Fever, Illness, Headache',
    consult_date='20-02-2023 9:00 AM',
    diagnosis_note="Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged.",
    advice_given = 'Avoid oily and spicy food',
    follow_up_date = '00/00/0000'

    pdf = FPDF()
    pdf.set_font('Arial', 'B', 7)
    pdf.add_page('P', (210, 320))

    pdf.image('logo1.png', x=10, y=15, w=40, h=20, type='', link='')

    # DoctorPersonalDetails.objects.get(id=consultation_id)

    print(consultation_id)
    doctor_details = DoctorConsultation.objects.get(id=consultation_id)
    userSerialData = ShowDoctorConsultationSerializer(doctor_details)
    data = userSerialData.data
    print(data)
    # appointments = json.loads(json.dumps(userSerialData.data))
    

    # f_name = data.firstname
    # print(f_name)
    name = data['doctor_id']['firstname'] + " " + data['doctor_id']['lastname']
    speciality = data['doctor_slot']['doctor']['speciality'] + " | Reg No" + data['doctor_slot']['doctor']['license_no']
    contact = data['doctor_id']['phone_no']
    mail = data['doctor_id']['email']
    patient = data['consultation_for']['full_name']
    gender = data['consultation_for']['gender']
    age = data['consultation_for']['age']
    date = data['appointment_date']
    slot = data['doctor_slot']['slots']
    mode = data['doctor_slot']['meeting_mode']
    reason = data['reason_for_consultation']
    note = data['dignosis']
    advice = data['advice']
    reschedule_date = data['reschedule_by']
    followup_date = data['next_appointment']
    # address = data['doctor_slot']['organization_id']['user_id']['street_name']

    # Header Info
    # Dr. Name
    pdf.set_xy(125, 20)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font(style='B', family='Arial', size=14)
    pdf.set_text_color(0, 0, 0)
    text = f"{name}"
    pdf.cell(w=30, h=10, txt=str(text), fill=True, align='L')

    # Dr. Qualification
    pdf.set_xy(125, 30)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = f"{speciality}"
    pdf.multi_cell(w=60, h=5, txt=str(text), fill= True, align='L')

    # Dr. Address
    # pdf.set_xy(125, 35)
    # pdf.set_fill_color(255,255,255)
    # pdf.set_font(style = '', family = 'Arial',  size = 10)
    # pdf.set_text_color(0,0,0)
    # text = dr_add
    # pdf.multi_cell(w=70, h=5, txt=str(text), fill= True, align='L')

    # Dr. Contact No.
    pdf.set_xy(125, 38)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Contact No.'
    pdf.multi_cell(w=40, h=5, txt=str(text), fill= True, align='L')

    pdf.set_xy(125, 43)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 12)
    pdf.set_text_color(0,0,0)
    text = f"{contact}"
    pdf.cell(w=40, h=5, txt=str(text), fill= True, align='L')

    # Dr. Email
    pdf.set_xy(160, 38)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'E-Mail'
    pdf.multi_cell(w=40, h=5, txt=str(text), fill= True, align='L')

    pdf.set_xy(160, 42)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 12)
    pdf.set_text_color(0,0,0)
    text = f"{mail}"
    pdf.cell(w=60, h=10, txt=str(text), fill= True, align='L')

    # Patient Details
    pdf.set_xy(10, 50)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 14)
    pdf.set_text_color(0,0,0)
    text = 'Patient Details'
    pdf.cell(w=70, h=10, txt=str(text).upper(), fill= True, align='L')

    # Separating line
    pdf.set_draw_color(0,0,0)
    pdf.line(10, 60, 200, 60)

    # Patient Name
    pdf.set_xy(10, 65)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Patient:'
    pdf.cell(w=15, h=8, txt=str(text), fill= True, align='L')

    pdf.set_xy(25, 65)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    # name = f
    gender = gender
    age = age
    text = f"{patient}" + ' | ' + f"{gender}" + ' | ' + f"{age}"
    pdf.cell(w=70, h=8, txt=str(text).upper(), fill= True, align='L')

    # Contact
    pdf.set_xy(10, 73)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Contact:'
    pdf.cell(w=15, h=8, txt=str(text), fill= True, align='L')

    pdf.set_xy(25, 73)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = contact
    pdf.cell(w=70, h=8, txt=str(text), fill= True, align='L')

    # Consult Type
    pdf.set_xy(10, 81)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Consult Type:'
    pdf.cell(w=20, h=8, txt=str(text), fill= True, align='L')

    pdf.set_xy(33, 81)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = f"{mode}"
    pdf.cell(w=70, h=8, txt=str(text), fill= True, align='L')

    # Consulting Reason
    pdf.set_xy(10, 89)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Consulting Reason:'
    pdf.cell(w=20, h=8, txt=str(text), fill= True, align='L')

    pdf.set_xy(43, 89)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = f"{reason}"
    pdf.cell(w=70, h=8, txt=str(text), fill= True, align='L')

    # Consult Date
    pdf.set_xy(140, 65)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Consult Date:'
    pdf.cell(w=15, h=8, txt=str(text), fill= True, align='L')

    pdf.set_xy(162, 65)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = f"{date} {slot}" 
    pdf.cell(w=70, h=8, txt=str(text), fill= True, align='L')

    # Diagnosis / Note
    pdf.set_xy(10, 100)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 14)
    pdf.set_text_color(0,0,0)
    text = 'Diagnosis Note'
    pdf.cell(w=20, h=10, txt=str(text).upper(), fill= True, align='L')

    # Separating line
    pdf.set_draw_color(0,0,0)
    pdf.line(10, 110, 200, 110)

    # Diagnosis Note
    pdf.set_xy(10, 115)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 8)
    pdf.set_text_color(0,0,0)
    text = f"{note}"
    pdf.multi_cell(w=190, h=5, txt=str(text).upper(), fill= True, align='L')

    # Medication Prescribed
    pdf.set_xy(10, 145)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 14)
    pdf.set_text_color(0,0,0)
    text = 'Medication Prescribed'
    pdf.multi_cell(w=190, h=5, txt=str(text).upper(), fill= True, align='L')

    # Table  Head Cells
    #Cell 1
    pdf.set_xy(10, 155 )
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    pdf.cell(w=29, h=10, txt='Medicine Name', fill= True, align='C', border=1)

    #Cell 2
    pdf.set_xy(39, 155)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    pdf.cell(w=28, h=10, txt='Quantity', fill= True, align='C', border=1)

    #Cell 3
    pdf.set_xy(67, 155)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    pdf.cell(w=29, h=10, txt='Doses', fill= True, align='C', border=1)

    # #Cell 4
    # pdf.set_xy(140, 155)
    # pdf.set_fill_color(255,255,255)
    # pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    # pdf.set_text_color(0,0,0)
    # pdf.cell(w=60, h=10, txt='Dose Type', fill= True, align='C', border=1)

    #Cell 5
    pdf.set_xy(95.5, 155)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    pdf.cell(w=32, h=10, txt='Frequency', fill= True, align='C', border=1)

    #Cell 6
    pdf.set_xy(127.5, 155)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    pdf.cell(w=32, h=10, txt='To be Taken', fill= True, align='C', border=1)

    #Cell 7
    pdf.set_xy(158.7, 155)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    pdf.cell(w=35, h=10, txt='Consumption Type', fill= True, align='C', border=1)


    # Table
    pdf.set_xy(3, 165 )
    pdf.set_font('Times','',10.0)
    pdf.set_text_color(0,0,0)
    pdf.set_fill_color(255, 255, 255) 

    # Effective page width, or just epw
    epw = pdf.w - 2*pdf.l_margin
    col_width = epw/6


    data = prescriptionData
    # print(data)
    tickets = prescriptionData
    print(tickets)
    # data = json.loads(tickets)
    # print(data[0])

    # Document title centered, 'B'old, 14 pt
    pdf.set_font('Times','B',14.0) 
    pdf.set_font('Times','',10.0)
    pdf.set_fill_color(255, 255, 255)

    pdf.ln(0.5)

    #Text height is the same as current font size
    th = 7

    # Calculate the total height required for the table
    table_height = len(data) * th

    # Check if the table exceeds the available space on the page
    if pdf.y + table_height > pdf.page_break_trigger:
        pdf.add_page()

    # Store the initial y position
    initial_y = pdf.y

    for row in tickets:
        count = 0
        print("dvdfdss"*80)
        print(row)
        for key in row.keys():
            print(key)
            # for value in row:
            pdf.set_fill_color(255, 255, 255)
            if count in [1]:
                pdf.cell(col_width*0.9, th, str(row[key]), border=1, fill= True)
            elif count in [2]:
                pdf.cell(col_width*0.9, th, str(row[key]), border=1, fill= True)
            elif count in [3]:
                print("----------------------------")
                print(row['dose_type'])
                merged_text = str(row[key]) + " " + str(row['dose_type'])
                pdf.cell(col_width*0.9, th, str(merged_text), border=1, fill= True)
            # elif count in [4]:
            #     pdf.cell(col_width*0.8, th, str(row[key]), border=1, fill= True)
            elif count in [5]:
                pdf.cell(col_width*1, th, str(row[key]), border=1, fill= True)
            elif count in [6]:
                pdf.cell(col_width*1, th, str(row[key]), border=1, fill= True)
            elif count in [7]:
                pdf.cell(col_width*1.1, th, str(row[key]), border=1, fill= True)
            count += 1
        pdf.ln(th)

    # Calculate the updated table height
    updated_table_height = len(data) * th

    # Calculate the difference in height
    height_difference = updated_table_height - table_height

    # Update the y position to increase the table height
    pdf.y = initial_y + height_difference

    # Advice Given
    pdf.set_xy(10, 250)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Advice Given:'
    pdf.cell(w=15, h=5, txt=str(text).upper(), fill= True, align='L')

    pdf.set_xy(10, 255)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = '- ' + f"{advice}"
    pdf.cell(w=70, h=5, txt=str(text), fill= True, align='L')

    # Follow Up Date
    pdf.set_xy(10, 265)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = 'Follow Up Date:'
    pdf.cell(w=15, h=5, txt=str(text).upper(), fill= True, align='L')

    pdf.set_xy(10, 270)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 10)
    pdf.set_text_color(0,0,0)
    text = f"{followup_date}"
    pdf.cell(w=70, h=5, txt=str(text), fill= True, align='L')

    # Disclaimer
    pdf.set_xy(10, 290)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = 'B', family = 'Arial',  size = 8)
    pdf.set_text_color(0,0,0)
    text = 'Disclaimer:' 
    pdf.cell(w=15, h=5, txt=str(text), fill= True, align='L')

    pdf.set_xy(30, 290)
    pdf.set_fill_color(255,255,255)
    pdf.set_font(style = '', family = 'Arial',  size = 8)
    pdf.set_text_color(0,0,0)
    text = "Confidentiality disclaimers, also known as email disclaimers, explain that some content is only intended to be seen by a certain audience for example, private information in an email."
    pdf.multi_cell(w=180, h=5, txt=str(text), fill= True, align='L')

    




    pdf_name = settings.MEDIA_ROOT + '/consultation/prescription/Prescription_'+ str(consultation_id)+'.pdf'
    pdf.output(pdf_name, 'F')
    return '/consultation/prescription/Prescription_'+ str(consultation_id)+'.pdf'