from django.shortcuts import render
from datetime import datetime
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
from datetime import datetime
import ipfsApi
import json
from web3 import Web3, HTTPProvider
import pickle
import time
import ecdsa
import hashlib
import pickle
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
import base64
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
import timeit
import matplotlib.pyplot as plt
import io
import base64

global username, doctor, ratingsList, prescriptionList, usersList
global contract, web3
api = ipfsApi.Client(host='http://127.0.0.1', port=5001)
propose_time = []
extension_time = []

def getECDSAKeys():
    if os.path.exists("keys/ecdsa.pckl") == False:
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        f = open("keys/ecdsa.pckl", "wb")
        pickle.dump(priv_key, f)
        f.close()
    else:
        f = open("keys/ecdsa.pckl", "rb")
        private_key = pickle.load(f)
        f.close()
    return private_key

def getRSAKeys():
    if os.path.exists("keys/rsa_public") == False:
        key = RSA.generate(2048)
        private_key = key.export_key('PEM')
        public_key = key.publickey().exportKey('PEM')
        with open("keys/rsa_public", "wb") as file:
            file.write(public_key)
        file.close()
        with open("keys/rsa_private", "wb") as file:
            file.write(private_key)
        file.close()
    else:
        with open("keys/rsa_public", "rb") as file:
            public_key = file.read()
        file.close()
        with open("keys/rsa_private", "rb") as file:
            private_key = file.read()
        file.close()
    return private_key, public_key    

#function to call contract
def getContract():
    global contract, web3
    blockchain_address = 'http://127.0.0.1:9545'
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'Healthcare.json' #Healthcare contract file
    deployed_contract_address = '0x3386973FE95f358937a8c15c9FcDBaD07D6C1dA1' #contract address
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  # load contract info as JSON
        contract_abi = contract_json['abi']  # fetch contract's abi - necessary to call its functions
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
getContract()

def getUsersList():
    global usersList, contract
    usersList = []
    count = contract.functions.getUserCount().call()
    for i in range(0, count):
        user = contract.functions.getUsername(i).call()
        password = contract.functions.getPassword(i).call()
        phone = contract.functions.getPhone(i).call()
        desc = contract.functions.getDescription(i).call()
        utype = contract.functions.getUserType(i).call()
        usersList.append([user, password, phone, desc, utype])

def getRatingsList():
    global ratingsList, contract
    ratingsList = []
    count = contract.functions.getRatingCount().call()
    for i in range(0, count):
        doc = contract.functions.getDoctorRating(i).call()
        usr = contract.functions.getUserRating(i).call()
        review = contract.functions.getReview(i).call()
        rating = contract.functions.getRating(i).call()
        rating_date = contract.functions.getRatingDate(i).call()
        ratingsList.append([doc, usr, review, float(rating), rating_date])

def getPrescriptionList():
    global prescriptionList, contract
    prescriptionList = []
    count = contract.functions.getEhrCount().call()
    for i in range(0, count):
        uname = contract.functions.getPatient(i).call()
        docname = contract.functions.getDoctor(i).call()
        disease = contract.functions.getDisease(i).call()
        report = contract.functions.getReport(i).call()
        prescription = contract.functions.getPrescription(i).call()
        ehr_date = contract.functions.getEhrDate(i).call()
        payment = contract.functions.getPayment(i).call()
        signature = contract.functions.getSignature(i).call()
        prescriptionList.append([uname, docname, disease, report, prescription, ehr_date, payment, signature])
getUsersList()
getRatingsList()    
getPrescriptionList()

def Graph(request):
    if request.method == 'GET':
        global propose_time, extension_time
        num = []
        for i in range(len(propose_time)):
            num.append((i+1))
        plt.plot(num, propose_time, label='Propose CA-DPPF')
        plt.plot(num, extension_time, label='Extension CHACHA20')
        plt.xlabel("Number of Transactions")
        plt.ylabel("Execution Time")
        plt.title("Execution Time Comparison Graph")
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        img_b64 = base64.b64encode(buf.getvalue()).decode()    
        context= {'data':'Execution Time Graph', 'img': img_b64}
        return render(request, 'PatientScreen.html', context)   

def getDoctorRating(name):
    global ratingsList
    rating = 5
    total = 0
    count = 0
    for i in range(len(ratingsList)):
        rl = ratingsList[i]
        if rl[0] == name:
            total += rl[3]
            count += 1
    if total > 0:
        rating = total / count
    return rating

def FeedbackAction(request):
    if request.method == 'POST':
        global username, ratingsList
        doctor = request.POST.get('t1', False)
        reviews = request.POST.get('t2', False)
        ratings = request.POST.get('t3', False)
        today = str(datetime.now())
        msg = contract.functions.saveRating(doctor, username, reviews, ratings, today).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
        ratingsList.append([doctor, username, reviews, float(ratings), today])
        context= {'data':'Your ratings accepted for doctor : '+doctor}
        return render(request, 'PatientScreen.html', context)               

def Feedback(request):
    if request.method == 'GET':
        global username, usersList
        output = '<tr><td><font size="3" color="black">Doctor&nbsp;Name</td><td><select name="t1">'
        for i in range(len(usersList)):
            ul = usersList[i]
            if ul[4] == 'Doctor':
                output += '<option value="'+ul[0]+'">'+ul[0]+'</option>'
        output += "</select></td></tr>"        
        context= {'data':output}        
        return render(request,'Feedback.html', context)

def ViewReport(request):
    if request.method == 'GET':
        global dec_time
        hashcode = request.GET.get('pid', False)
        filename = request.GET.get('file', False)
        content = api.get_pyobj(hashcode)
        response = HttpResponse(content,content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename='+filename
        return response

def GeneratePrescriptionAction(request):
    if request.method == 'POST':
        global prescriptionList
        pid = request.POST.get('t1', False)
        prescription = request.POST.get('t2', False)
        filename = request.FILES['t3'].name
        myfile = request.FILES['t3'].read()
        hashcode = api.add_pyobj(myfile)
        contract.functions.updatePrescription(int(pid), prescription+"#"+filename+"#"+hashcode).transact()
        pl = prescriptionList[int(pid)]
        pl[4] = prescription+"#"+filename+"#"+hashcode
        data = "Prescription Updated Successfully"
        context= {'data':data}
        return render(request,'DoctorScreen.html', context)

def GeneratePrescription(request):
    if request.method == 'GET':
        global username
        pid = request.GET['pid']
        output = '<tr><td><font size="3" color="black">Appointment&nbsp;ID</td><td><input type="text" name="t1" size="25" value="'+pid+'" readonly/></td></tr>'
        context= {'data':output}
        return render(request,'GeneratePrescription.html', context)    
    
def ViewAppointments(request):
    if request.method == 'GET':
        global username, prescriptionList
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Appointment ID</font></th>'
        output+='<th><font size=3 color=black>Patient Name</font></th>'
        output+='<th><font size=3 color=black>Doctor Name</font></th>'
        output+='<th><font size=3 color=black>Disease Details</font></th>'
        output+='<th><font size=3 color=black>Hashcode & Report Name</font></th>'
        output+='<th><font size=3 color=black>Prescription</font></th>'
        output+='<th><font size=3 color=black>Booking Date</font></th>'
        output+='<th><font size=3 color=black>Payment</font></th>'
        output+='<th><font size=3 color=black>ECDSA Signature</font></th>'
        output+='<th><font size=3 color=black>View Report</font></th>'
        output+='<th><font size=3 color=black>Generate Pescription</font></th></tr>'
        private_key, public_key = getRSAKeys()
        for i in range(len(prescriptionList)):
            pl = prescriptionList[i]
            if pl[1] == username:
                hashcode = pl[3]
                hashcode = hashcode.split("@")
                rsa_private_key = RSA.importKey(private_key)
                rsa_private_key = PKCS1_OAEP.new(rsa_private_key)
                disease = base64.b64decode(pl[2])
                disease = rsa_private_key.decrypt(disease)
                output+='<tr><td><font size=3 color=black>'+str(i+1)+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[0])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[1])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(disease.decode())+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[3][0:15])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[4])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[5])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[6])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(pl[7])+'</font></td>'
                output+='<td><a href=\'ViewReport?pid='+str(hashcode[0])+'&file='+hashcode[1]+'\'><font size=3 color=black>Click Here</font></a></td>'                
                if pl[4] == 'None':
                    output+='<td><a href=\'GeneratePrescription?pid='+str(i)+'\'><font size=3 color=black>Click Here for Prescription</font></a></td></tr>'
                else:
                    output+='<td><font size=3 color=black>'+pl[4]+'</font></td></tr>'
        context= {'data':output}            
        return render(request,'DoctorScreen.html', context)                
        
def ViewPrescription(request):
    if request.method == 'GET':
        global prescriptionList, username
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Patient Name</font></th>'
        output+='<th><font size=3 color=black>Doctor Name</font></th>'
        output+='<th><font size=3 color=black>Disease Details</font></th>'
        output+='<th><font size=3 color=black>IPFS Report Hashcode</font></th>'
        output+='<th><font size=3 color=black>Report Name</font></th>'
        output+='<th><font size=3 color=black>Prescription</font></th>'
        output+='<th><font size=3 color=black>Prescription File Name</font></th>'
        output+='<th><font size=3 color=black>Download Prescription</font></th>'
        output+='<th><font size=3 color=black>Date</font></th>'
        output+='<th><font size=3 color=black>Payment</font></th>'
        output+='<th><font size=3 color=black>Digital Signature</font></th></tr>'
        private_key, public_key = getRSAKeys()
        for i in range(len(prescriptionList)):
            pl = prescriptionList[i]
            if pl[0] == username:
                hashcode = pl[3]
                hashcode = hashcode.split("@")
                prescription = pl[4]
                print(prescription)
                pres = "None"
                fname = "-"
                file_hash = "-"
                if prescription != 'None':
                    arr = prescription.split("#")
                    pres = arr[0]
                    fname = arr[1]
                    file_hash = arr[2]
                rsa_private_key = RSA.importKey(private_key)
                rsa_private_key = PKCS1_OAEP.new(rsa_private_key)
                disease = base64.b64decode(pl[2])
                disease = rsa_private_key.decrypt(disease)    
                output+='<tr><td><font size=3 color=black>'+pl[0]+'</font></td>'
                output+='<td><font size=3 color=black>'+pl[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+disease.decode()+'</font></td>'
                output+='<td><font size=3 color=black>'+hashcode[0][0:10]+'</font></td>'
                output+='<td><font size=3 color=black>'+hashcode[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+pres+'</font></td>'
                output+='<td><font size=3 color=black>'+fname+'</font></td>'
                if prescription == 'None':
                    output+='<td><font size=3 color=black>Pending</font></td>'
                else:
                    output+='<td><a href=\'ViewReport?pid='+str(file_hash)+'&file='+fname+'\'><font size=3 color=black>Click Here</font></a></td>'
                output+='<td><font size=3 color=black>'+pl[5]+'</font></td>'
                if len(pl) >= 6:
                    output+='<td><font size=3 color=black>'+pl[6]+'</font></td>'
                else:
                    output+='<td><font size=3 color=black>-</font></td></tr>'
                if len(pl) >= 7:
                    output+='<td><font size=3 color=black>'+pl[7]+'</font></td></tr>'
                else:
                    output+='<td><font size=3 color=black>-</font></td></tr>'
        output += "</table><br/><br/><br/><br/>"
        context= {'data':output}        
        return render(request,'PatientScreen.html', context)      

def AppointmentAction(request):
    if request.method == 'POST':
        global username, propose_time, extension_time
        doctor = request.POST.get('t1', False)
        patient = request.POST.get('t2', False)
        disease = request.POST.get('t3', False)
        plain_disease = request.POST.get('t3', False)
        payment = request.POST.get('t4', False)
        today = str(datetime.now())
        filename = request.FILES['t5'].name
        myfile = request.FILES['t5'].read()
        hashcode = api.add_pyobj(myfile)
        start = timeit.default_timer()
        private_key, public_key = getRSAKeys()
        rsa_public_key = RSA.importKey(public_key)
        rsa_public_key = PKCS1_OAEP.new(rsa_public_key)
        disease = rsa_public_key.encrypt(disease.encode())
        disease = base64.b64encode(disease).decode()
        end = timeit.default_timer()
        propose_time.append(end - start)

        start = timeit.default_timer()
        cha_key = get_random_bytes(32)
        cha_cipher = ChaCha20.new(key=cha_key)
        chacha_encrypt = cha_cipher.encrypt(plain_disease.encode())
        end = timeit.default_timer()
        extension_time.append(end - start)

        signature_key = getECDSAKeys()
        public_key = signature_key.get_verifying_key()
        message_hash = hashlib.sha256(plain_disease.encode()).digest()
        signature = signature_key.sign(message_hash)
        signature = hashlib.sha256(signature).hexdigest()

        for i in range(0, 5):
            start = timeit.default_timer()
            private_key, public_key = getRSAKeys()
            rsa_public_key = RSA.importKey(public_key)
            rsa_public_key = PKCS1_OAEP.new(rsa_public_key)
            disease1 = rsa_public_key.encrypt(plain_disease.encode())
            disease1 = base64.b64encode(disease1).decode()
            end = timeit.default_timer()
            propose_time.append(end - start)

            start = timeit.default_timer()
            cha_key = get_random_bytes(32)
            cha_cipher = ChaCha20.new(key=cha_key)
            chacha_encrypt = cha_cipher.encrypt(plain_disease.encode())
            end = timeit.default_timer()
            extension_time.append(end - start)
        
        msg = contract.functions.saveEhr(patient, doctor, disease, hashcode+"@"+filename, 'None', today, payment, signature).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
        prescriptionList.append([patient, doctor, disease, hashcode+"@"+filename, 'None', today])
        context= {'data':'Your Appointment Confirmed with Doctor : '+doctor+'<br/>Appointment ID : '+str(len(prescriptionList))+'<br/>'+str(tx_receipt)}
        return render(request, 'PatientScreen.html', context)        

def Appointment(request):
    if request.method == 'GET':
        global username
        doctor = request.GET['doctor']
        today = datetime.now()
        month = today.month
        year = today.year
        day = today.day
        output = '<tr><td><font size="3" color="black">Doctor&nbsp;Name</td><td><input type="text" name="t1" size="25" value="'+doctor+'" readonly/></td></tr>'
        output += '<tr><td><font size="3" color="black">Patient&nbsp;Name</td><td><input type="text" name="t2" size="25" value="'+username+'" readonly/></td></tr>'
        output += '<tr><td><font size="3" color="black">Disease&nbsp;Details</td><td><input type="text" name="t3" size="40" /></td></tr>'
        output += '<tr><td><font size="3" color="black">Payment&nbsp;Fee</td><td><input type="text" name="t4" size="15" value="500"/></td></tr>'
        output += '<tr><td><font size="3" color="black">Upload&nbsp;Medical&nbsp;Report</td><td><input type="file" name="t5" size="40" /></td></tr>'
        context= {'data':output}
        return render(request,'BookAppointment.html', context)      

def BookAppointment(request):
    if request.method == 'GET':
        global usersList
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Doctor Name</font></th>'
        output+='<th><font size=3 color=black>Phone No</font></th>'
        output+='<th><font size=3 color=black>Description</font></th>'
        output+='<th><font size=3 color=black>Rating</font></th>'
        output+='<th><font size=3 color=black>Book Appointment</font></th></tr>'
        for i in range(len(usersList)):
            ul = usersList[i]
            if ul[4] == 'Doctor':
                rating = getDoctorRating(ul[0])
                output+='<tr><td><font size=3 color=black>'+ul[0]+'</font></td>'
                output+='<td><font size=3 color=black>'+ul[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+ul[3]+'</font></td>'
                output+='<td><font size=3 color=black>'+str(rating)+'</font></td>'
                output+='<td><a href=\'Appointment?doctor='+ul[0]+'\'><font size=3 color=black>Click Here to Book Appointment</font></a></td></tr>'
        output += "</table><br/><br/><br/><br/>"
        context= {'data':output}        
        return render(request,'PatientScreen.html', context)      

def index(request):
    if request.method == 'GET':
        return render(request,'index.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})
    
def DoctorLogin(request):
    if request.method == 'GET':
       return render(request, 'DoctorLogin.html', {})

def PatientLogin(request):
    if request.method == 'GET':
       return render(request, 'PatientLogin.html', {})

def isUserExists(username):
    is_user_exists = False
    global details
    mysqlConnect = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'doctorpatientapp',charset='utf8')
    with mysqlConnect:
        result = mysqlConnect.cursor()
        result.execute("select * from user_signup where username='"+username+"'")
        lists = result.fetchall()
        for ls in lists:
            is_user_exists = True
    return is_user_exists    

def RegisterAction(request):
    if request.method == 'POST':
        global usersList
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        desc = request.POST.get('t6', False)
        usertype = request.POST.get('t8', False)
        count = contract.functions.getUserCount().call()
        status = "none"
        for i in range(0, count):
            user1 = contract.functions.getUsername(i).call()
            if username == user1:
                status = "exists"
                break
        if status == "none":
            msg = contract.functions.saveUser(username, password, contact, desc, usertype).transact()
            tx_receipt = web3.eth.waitForTransactionReceipt(msg)
            usersList.append([username, password, contact, desc, usertype])
            context= {'data':'Signup Process Completed<br/>'+str(tx_receipt)}
            return render(request, 'Register.html', context)
        else:
            context= {'data':'Given username already exists'}
            return render(request, 'Register.html', context)

def PatientLoginAction(request):
    if request.method == 'POST':
        global username, contract, usersList
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status = 'none'
        for i in range(len(usersList)):
            ulist = usersList[i]
            user1 = ulist[0]
            pass1 = ulist[1]
            utype = ulist[4]
            if user1 == username and pass1 == password and utype == "Patient":
                status = "success"
                break
        if status == 'success':
            output = 'Welcome '+username
            context= {'data':output}
            return render(request, "PatientScreen.html", context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'PatientLogin.html', context)
        
def DoctorLoginAction(request):
    if request.method == 'POST':
        global username, contract, usersList
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status = 'none'
        for i in range(len(usersList)):
            ulist = usersList[i]
            user1 = ulist[0]
            pass1 = ulist[1]
            utype = ulist[4]
            if user1 == username and pass1 == password and utype == "Doctor":
                status = "success"
                break
        if status == 'success':
            output = 'Welcome '+username
            context= {'data':output}
            return render(request, "DoctorScreen.html", context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'DoctorLogin.html', context)










        


        
