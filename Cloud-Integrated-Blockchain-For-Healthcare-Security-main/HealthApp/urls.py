from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
	       path('DoctorLogin.html', views.DoctorLogin, name="DoctorLogin"), 
	       path('PatientLogin.html', views.PatientLogin, name="PatientLogin"), 
	       path('Register.html', views.Register, name="Register"),
	       path('RegisterAction', views.RegisterAction, name="RegisterAction"),	
	       path('BookAppointment', views.BookAppointment, name="BookAppointment"),
	       path('AppointmentAction', views.AppointmentAction, name="AppointmentAction"),
	       path('Appointment', views.Appointment, name="Appointment"),
	       path('ViewPrescription', views.ViewPrescription, name="ViewPrescription"),
	       path('ViewAppointments', views.ViewAppointments, name="ViewAppointments"),
	       path('GeneratePrescription', views.GeneratePrescription, name="GeneratePrescription"),
	       path('GeneratePrescriptionAction', views.GeneratePrescriptionAction, name="GeneratePrescriptionAction"),
	       path('DoctorLoginAction', views.DoctorLoginAction, name="DoctorLoginAction"), 
	       path('PatientLoginAction', views.PatientLoginAction, name="PatientLoginAction"), 	
	       path('Feedback.html', views.Feedback, name="Feedback"),
	       path('FeedbackAction', views.FeedbackAction, name="FeedbackAction"),	
	       path('ViewReport', views.ViewReport, name="ViewReport"),	
	       path('Graph', views.Graph, name="Graph"),
]
