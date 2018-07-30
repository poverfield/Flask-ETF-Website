# Small Cap Email
# Purpose: notify through email what stocks to buy after market closes
# Run daily at same time as small_cap.R


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import os
import time

time.sleep(90) # sleep 90 seconds to allow Rscript to run

# Change directory path
path = '/home/pi/Desktop/files'
os.chdir(path)

# Read in account information
f = open('account.txt') # read in account.txt
f_lines = f.readlines()
email = f_lines[0].split(': ',1)[1][0:len(f_lines[0].split(': ',1)[1])-1] # email address (send and recieve)
password = f_lines[1].split(': ',1)[1][0:len(f_lines[1].split(': ',1)[1])-1] # email password
f.close()

# Email Function
def send_email(file): # function with input 'buy/sell/close'
    sender = email
    receiver = email

    msg = MIMEMultipart()
    msg['Subject'] = 'Small Cap Trade'
    msg['From'] = sender
    msg['To'] = receiver
    #file = 'plot.png'
    stock_name = file[:file.index('.')]

    now = str(datetime.datetime.now())
    now_date = now[0:16]
    
    message = 'Time stamp: ' + now_date + '\n\n' + 'Action: Buy ' + stock_name
    msg.attach(MIMEText(message))
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(open(file, 'rb').read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file))
    msg.attach(attachment)
    s = server = smtplib.SMTP('smtp.gmail.com:587') #smtp.gmail.com:587
    s.starttls()
    s.login(sender, password)
    s.sendmail(sender, receiver, msg.as_string())
    s.quit()

    # remove file
    os.remove(file)
    print('sent ' + stock_name)


# get .png files
def file_func():
    files = os.listdir()
    for i in files:
        if '.png' in i:
            file.append(i)
    return(file)



# get images
file = []
file_func()

# email images if image to send
if len(file) >= 1:
    for i in file:
        send_email(i)



