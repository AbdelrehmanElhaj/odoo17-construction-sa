#!/usr/bin/env python3
"""
Generate ar_SA.po from school_management.pot with complete Arabic translations.
Usage: python3 build_ar_po.py
"""

import re
import os

POT = "addons/school_management/i18n/school_management.pot"
OUT = "addons/school_management/i18n/ar_SA.po"

# ─────────────────────────────────────────────────────────────────────────────
# Arabic translation table – all single-line msgids
# ─────────────────────────────────────────────────────────────────────────────
TRANSLATIONS = {
    # ── Menus ──────────────────────────────────────────────────────────────
    "School Management": "إدارة المدرسة",
    "Dashboard": "لوحة المعلومات",
    "Students": "الطلاب",
    "All Students": "جميع الطلاب",
    "Guardians": "أولياء الأمور",
    "Teachers": "المعلمون",
    "All Teachers": "جميع المعلمين",
    "Subjects": "المواد الدراسية",
    "Classes": "الفصول الدراسية",
    "All Classes": "جميع الفصول",
    "Attendance": "الحضور والغياب",
    "Take Attendance": "تسجيل الحضور",
    "Attendance Records": "سجلات الحضور",
    "Grades & Exams": "الدرجات والاختبارات",
    "Exams": "الاختبارات",
    "Grades": "الدرجات",
    "Fees": "الرسوم المدرسية",
    "Student Fees": "رسوم الطلاب",
    "Payments": "المدفوعات",
    "Communication": "التواصل",
    "Announcements": "الإعلانات",
    "Send Parent Email": "إرسال بريد إلكتروني لأولياء الأمور",
    "Timetables": "الجداول الدراسية",
    "Class Timetables": "جداول الفصول",
    "Teacher Schedules": "جداول المعلمين",
    "Analytics": "التحليلات",
    "Student Analysis": "تحليل الطلاب",
    "Attendance Analysis": "تحليل الحضور",
    "Grade Analysis": "تحليل الدرجات",
    "Fee Analysis": "تحليل الرسوم",
    "Configuration": "الإعدادات",
    "Academic Years": "السنوات الدراسية",
    "Fee Types": "أنواع الرسوم",
    "School Periods": "الحصص الدراسية",
    "School Branches": "فروع المدرسة",

    # ── Model descriptions ──────────────────────────────────────────────────
    "School Branch / Campus": "فرع المدرسة / الحرم الجامعي",
    "School Dashboard": "لوحة معلومات المدرسة",
    "Student Attendance": "حضور الطالب",
    "Student Grade": "درجة الطالب",
    "Student Fee": "رسوم الطالب",
    "Bulk Attendance Wizard": "معالج الحضور الجماعي",
    "Bulk Attendance Line": "سطر الحضور الجماعي",
    "Bulk Grade Entry Wizard": "معالج إدخال الدرجات الجماعي",
    "Bulk Grade Entry Line": "سطر إدخال الدرجات الجماعي",
    "Class Timetable": "جدول الفصل الدراسي",
    "Timetable Slot": "خانة الجدول الدراسي",
    "School Period": "الحصة الدراسية",
    "School Announcement": "الإعلان المدرسي",
    "Fee Payment": "دفع الرسوم",
    "Fee Type": "نوع الرسم",
    "Classroom": "الفصل الدراسي",
    "Academic Year": "السنة الدراسية",
    "Subject": "المادة الدراسية",
    "Teacher": "المعلم",
    "Guardian / Parent": "ولي الأمر",
    "Register Fee Payment Wizard": "معالج تسجيل دفع الرسوم",
    "School Communication Wizard": "معالج التواصل المدرسي",
    "Exam": "الاختبار",
    "Timetable": "الجدول الدراسي",
    "Announcement": "الإعلان",

    # ── Field labels – Student ──────────────────────────────────────────────
    "Full Name": "الاسم الكامل",
    "Student Full Name": "اسم الطالب الكامل",
    "Student ID": "رقم الطالب",
    "Student ID:": "رقم الطالب:",
    "Date of Birth": "تاريخ الميلاد",
    "Age": "العمر",
    "Gender": "الجنس",
    "Nationality": "الجنسية",
    "National ID": "رقم الهوية الوطنية",
    "Photo": "الصورة",
    "Notes": "ملاحظات",
    "Class": "الفصل الدراسي",
    "Grade Level": "المرحلة الدراسية",
    "School": "المدرسة",
    "Enrollment Date": "تاريخ القيد",
    "Status": "الحالة",
    "Guardian/Parent": "ولي الأمر",
    "Guardian Name": "اسم ولي الأمر",
    "Guardian Phone": "هاتف ولي الأمر",
    "Email": "البريد الإلكتروني",
    "Phone": "الهاتف",
    "Address": "العنوان",
    "Student List": "قائمة الطلاب",
    "Children List": "قائمة الأبناء",
    "Children": "الأبناء",
    "Portal User": "مستخدم البوابة",
    "Relationship": "صلة القرابة",

    # ── Field labels – Teacher / Subject ────────────────────────────────────
    "Teacher Full Name": "اسم المعلم الكامل",
    "Employee ID": "رقم الموظف",
    "School / Campus": "المدرسة / الحرم",
    "Specialization": "التخصص",
    "Qualification": "المؤهل العلمي",
    "Hire Date": "تاريخ التعيين",
    "Assigned Classes": "الفصول المُعيَّنة",
    "Mobile": "الجوال",
    "System User": "مستخدم النظام",
    "Subject Name": "اسم المادة الدراسية",
    "Subject Code": "رمز المادة",
    "Description": "الوصف",
    "Subjects & Classes": "المواد والفصول",
    "Subjects Taught": "المواد التي يُدرِّسها",

    # ── Field labels – Class ─────────────────────────────────────────────────
    "Section": "الشعبة",
    "Class Name": "اسم الفصل",
    "Capacity": "الطاقة الاستيعابية",
    "Room Number": "رقم الغرفة",
    "Supervisor Teacher": "المعلم المشرف",
    "Class Details": "تفاصيل الفصل",
    "Room Information": "معلومات الغرفة",

    # ── Field labels – Academic Year ────────────────────────────────────────
    "Academic Year Name": "اسم السنة الدراسية",
    "Code": "الرمز",
    "Start Date": "تاريخ البداية",
    "End Date": "تاريخ النهاية",
    "Current Year": "السنة الحالية",
    "Class List": "قائمة الفصول",

    # ── Field labels – Attendance ───────────────────────────────────────────
    "Reference": "المرجع",
    "Date": "التاريخ",
    "Recorded By": "سجّل بواسطة",
    "Attendance Info": "معلومات الحضور",

    # ── Field labels – Exam / Grade ─────────────────────────────────────────
    "Exam Name": "اسم الاختبار",
    "Exam Date": "تاريخ الاختبار",
    "Maximum Score": "الدرجة الكاملة",
    "Pass Score": "درجة النجاح",
    "Score": "الدرجة",
    "Max Score": "الدرجة الكاملة",
    "Percentage (%)": "النسبة المئوية (%)",
    "Grade": "التقدير",
    "Passed": "ناجح",
    "Rank": "الترتيب",
    "Student & Exam": "الطالب والاختبار",
    "Exam Details": "تفاصيل الاختبار",
    "Scoring": "التقييم",
    "Grades (field)": "الدرجات",

    # ── Field labels – Fee ──────────────────────────────────────────────────
    "Fee ID": "رقم الرسم",
    "Fee ID:": "رقم الرسم:",
    "Guardian": "ولي الأمر",
    "Currency": "العملة",
    "Amount Due": "المبلغ المستحق",
    "Amount Paid": "المبلغ المدفوع",
    "Balance": "الرصيد",
    "Due Date": "تاريخ الاستحقاق",
    "Default Amount": "المبلغ الافتراضي",
    "Active": "نشط",
    "Student & Fee": "الطالب والرسم",
    "Financial": "المالية",
    "Invoice Date": "تاريخ الفاتورة",

    # ── Field labels – Fee Payment ──────────────────────────────────────────
    "Receipt No.": "رقم الإيصال",
    "Payment Date": "تاريخ الدفع",
    "Payment Method": "طريقة الدفع",
    "Received By": "استُلم بواسطة",
    "Amount": "المبلغ",
    "Payment Details": "تفاصيل الدفع",
    "Fee Information": "معلومات الرسم",
    "Payment": "الدفع",
    "Fee Amount": "مبلغ الرسم",
    "Outstanding Balance": "الرصيد المتبقي",
    "Payment Amount": "مبلغ الدفع",
    "Outstanding Balance:": "الرصيد المتبقي:",

    # ── Field labels – Timetable ────────────────────────────────────────────
    "Period Name": "اسم الحصة",
    "Start Time": "وقت البدء",
    "End Time": "وقت الانتهاء",
    "Start": "البداية",
    "End": "النهاية",
    "Break / Recess": "استراحة",
    "Day": "اليوم",
    "Period": "الحصة",
    "Room": "الغرفة",
    "Weekly Grid": "الجدول الأسبوعي",
    "Slots": "الحصص",
    "Teacher Schedule": "جدول المعلم",

    # ── Field labels – Communication / Branch ──────────────────────────────
    "School Name": "اسم المدرسة",
    "School / Campus": "المدرسة / الحرم",
    "Logo": "الشعار",
    "Website": "الموقع الإلكتروني",
    "Principal": "مدير المدرسة",
    "Title": "العنوان",
    "Content": "المحتوى",
    "Publish Date": "تاريخ النشر",
    "Expiry Date": "تاريخ الانتهاء",
    "Audience": "الجمهور المستهدف",
    "Target Classes": "الفصول المستهدفة",
    "Email Sent": "تم الإرسال",
    "Recipients": "المستلمون",
    "Attachments": "المرفقات",

    # ── Field labels – Dashboard ────────────────────────────────────────────
    "Active Students": "الطلاب النشطون",
    "New This Month": "جدد هذا الشهر",
    "Male": "ذكر",
    "Female": "أنثى",
    "Active Teachers": "المعلمون النشطون",
    "Open Classes": "الفصول المفتوحة",
    "Today %": "نسبة اليوم",
    "This Week %": "نسبة الأسبوع",
    "Absent Today": "غائبو اليوم",
    "Total Billed": "إجمالي الفواتير",
    "Collected": "المحصَّل",
    "Outstanding": "المتبقي",
    "Collection Rate %": "نسبة التحصيل",
    "Overdue Fees": "رسوم متأخرة",
    "Avg Grade %": "متوسط الدرجات",
    "Pass Rate %": "نسبة النجاح",
    "Grade Entries": "إدخالات الدرجات",
    "This Week Attendance": "حضور هذا الأسبوع",

    # ── Form view group headers / buttons ───────────────────────────────────
    "Personal Information": "المعلومات الشخصية",
    "Academic Information": "المعلومات الأكاديمية",
    "Contact & Guardian": "التواصل وولي الأمر",
    "Contact": "التواصل",
    "Professional Information": "المعلومات المهنية",
    "Confirm": "تأكيد",
    "Cancel": "إلغاء",
    "Withdraw": "انسحاب",
    "Re-activate": "إعادة تفعيل",
    "Transfer": "نقل",
    "Activate": "تفعيل",
    "Close Year": "إغلاق السنة",
    "Reset to Draft": "إعادة للمسودة",
    "Enter Grades": "إدخال الدرجات",
    "Save Grades": "حفظ الدرجات",
    "Save Attendance": "حفظ الحضور",
    "Register Payment": "تسجيل الدفع",
    "Confirm Payment": "تأكيد الدفع",
    "Create Invoice": "إنشاء فاتورة",
    "Send Reminder": "إرسال تذكير",
    "Send Absence Alert": "إرسال تنبيه غياب",
    "Print Timetable": "طباعة الجدول",
    "Print Receipt": "طباعة الإيصال",
    "Publish": "نشر",
    "Send Email Now": "إرسال البريد الآن",
    "Archive": "أرشفة",
    "Send Email": "إرسال بريد إلكتروني",
    "Send Parent Communication": "إرسال رسالة لأولياء الأمور",
    "Grade Report": "تقرير الدرجات",
    "Certificate": "الشهادة",
    "Fee Statement": "كشف الرسوم",
    "Enrollment Certificate": "شهادة قيد",
    "Completion Certificate": "شهادة إتمام",
    "Payment Receipt": "إيصال دفع",

    # ── Search / filters ────────────────────────────────────────────────────
    "Search Students": "البحث عن طلاب",
    "Search Teachers": "البحث عن معلمين",
    "Search Classes": "البحث عن فصول",
    "Search Fees": "البحث عن رسوم",
    "Search Grades": "البحث عن درجات",
    "Search Exams": "البحث عن اختبارات",
    "Search Attendance": "البحث في الحضور",
    "Search Branches": "البحث عن فروع",
    "Search Academic Years": "البحث عن سنوات دراسية",
    "Withdrawn": "منسحب",
    "Transferred": "محوّل",
    "Graduated": "متخرج",
    "Inactive": "غير نشط",
    "Open": "مفتوح",
    "Closed": "مغلق",
    "Draft": "مسودة",
    "Confirmed": "مؤكد",
    "Graded": "مُرصَّد",
    "Closed": "مغلق",
    "Due": "مستحق",
    "Overdue": "متأخر",
    "Partially Paid": "مدفوع جزئياً",
    "Paid": "مدفوع",
    "Cancelled": "ملغى",
    "Present": "حاضر",
    "Absent": "غائب",
    "Late": "متأخر",
    "Excused": "بعذر",
    "Today": "اليوم",
    "This Week": "هذا الأسبوع",
    "First Term": "الفصل الأول",
    "Second Term": "الفصل الثاني",
    "Third Term": "الفصل الثالث",
    "Annual": "سنوي",
    "Current": "الحالي",
    "Passed": "ناجح",
    "Failed": "راسب",
    "Unpaid": "غير مدفوع",
    "Published": "منشور",
    "Archived": "مؤرشف",
    "Group By": "تجميع حسب",
    "Teacher (filter)": "المعلم",
    "Active (filter)": "نشط",

    # ── Selection values ────────────────────────────────────────────────────
    "Father": "الأب",
    "Mother": "الأم",
    "Other": "أخرى",
    "KG 1": "روضة 1",
    "KG 2": "روضة 2",
    "Grade 1": "الصف الأول الابتدائي",
    "Grade 2": "الصف الثاني الابتدائي",
    "Grade 3": "الصف الثالث الابتدائي",
    "Grade 4": "الصف الرابع الابتدائي",
    "Grade 5": "الصف الخامس الابتدائي",
    "Grade 6": "الصف السادس الابتدائي",
    "Grade 7": "الصف الأول المتوسط",
    "Grade 8": "الصف الثاني المتوسط",
    "Grade 9": "الصف الثالث المتوسط",
    "Grade 10": "الصف الأول الثانوي",
    "Grade 11": "الصف الثاني الثانوي",
    "Grade 12": "الصف الثالث الثانوي",
    "Midterm": "منتصف الفصل",
    "Final": "نهائي",
    "Quiz": "اختبار قصير",
    "Assignment": "واجب",
    "Practical": "عملي",
    "Cash": "نقداً",
    "Bank Transfer": "تحويل بنكي",
    "Cheque": "شيك",
    "Online": "دفع إلكتروني",
    "Everyone": "الجميع",
    "Parents Only": "أولياء الأمور فقط",
    "Teachers Only": "المعلمون فقط",
    "Students Only": "الطلاب فقط",
    "Sunday": "الأحد",
    "Monday": "الاثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",

    # ── Days of week (full forms in some places) ─────────────────────────────
    "Sun": "أح",
    "Mon": "إث",
    "Tue": "ثل",
    "Wed": "أر",
    "Thu": "خم",

    # ── Security groups ──────────────────────────────────────────────────────
    "Administrator": "مدير النظام",
    "Student Affairs": "شؤون الطلاب",
    "Parent / Guardian": "ولي الأمر",
    "School Management (module category)": "إدارة المدرسة",

    # ── Data records (translate=True fields) ────────────────────────────────
    "Tuition Fee": "رسوم الدراسة",
    "Registration Fee": "رسوم التسجيل",
    "Activity Fee": "رسوم الأنشطة",
    "Transport Fee": "رسوم النقل المدرسي",
    "Books & Materials": "الكتب والمستلزمات الدراسية",
    "Exam Fee": "رسوم الاختبارات",
    "Main School": "المدرسة الرئيسية",
    "North Campus": "الحرم الشمالي",
    "Period 1": "الحصة الأولى",
    "Period 2": "الحصة الثانية",
    "Period 3": "الحصة الثالثة",
    "Period 4": "الحصة الرابعة",
    "Period 5": "الحصة الخامسة",
    "Period 6": "الحصة السادسة",
    "Period 7": "الحصة السابعة",
    "Break": "الاستراحة",
    "Long Break": "الفسحة الكبرى",

    # ── Report labels ────────────────────────────────────────────────────────
    "Academic Grade Report": "تقرير الدرجات الأكاديمية",
    "Attendance Report": "تقرير الحضور والغياب",
    "Academic Year:": "السنة الدراسية:",
    "Student Name:": "اسم الطالب:",
    "Student:": "الطالب:",
    "Class:": "الفصل:",
    "Grade Level:": "المرحلة:",
    "Teacher:": "المعلم:",
    "Print Date:": "تاريخ الطباعة:",
    "Guardian:": "ولي الأمر:",
    "Guardian Phone:": "هاتف ولي الأمر:",
    "TOTAL": "الإجمالي",
    "AMOUNT PAID": "المبلغ المدفوع",
    "Total Fee:": "إجمالي الرسوم:",
    "Total Paid:": "إجمالي المدفوع:",
    "Attendance Rate": "نسبة الحضور",
    "Summary:": "الملخص:",
    "Passed:": "ناجح:",
    "Average:": "المتوسط:",
    "No grades recorded for this student.": "لا توجد درجات مسجلة لهذا الطالب.",
    "No attendance records found.": "لم يتم العثور على سجلات حضور.",
    "No fee records found.": "لم يتم العثور على سجلات رسوم.",
    "No fees created yet": "لم يتم إنشاء رسوم بعد",
    "Class Teacher": "معلم الفصل",
    "School Stamp": "ختم المدرسة",
    "Cashier Signature": "توقيع أمين الصندوق",
    "This is a computer-generated receipt. Thank you for your payment.": "هذا إيصال صادر إلكترونياً. شكراً لسدادكم.",
    "PAYMENT RECEIPT": "إيصال دفع",
    "Receipt No:": "رقم الإيصال:",
    "Payment Date:": "تاريخ الدفع:",
    "Student Name: (receipt)": "اسم الطالب:",
    "Fee Type:": "نوع الرسم:",
    "Fee Reference:": "مرجع الرسم:",
    "Payment Method:": "طريقة الدفع:",
    "Received By:": "استُلم بواسطة:",
    "Class Timetable": "جدول الفصل الدراسي",
    "Reference:": "المرجع:",
    "Notes:": "ملاحظات:",
    "Certificate of Enrollment": "شهادة قيد",
    "Certificate of Completion": "شهادة إتمام الدراسة",
    "This is to certify that": "نشهد بأن",
    "This certifies that": "يُشهد بأن",
    "is duly enrolled in": "مقيّد بصفة رسمية في",
    "for the academic year": "للعام الدراسي",
    "Enrollment Date:": "تاريخ القيد:",
    "Status:": "الحالة:",
    "Issued on:": "صدرت في:",
    "School Principal": "مدير المدرسة",
    "School Seal": "ختم المدرسة",
    "has successfully completed": "أتمّ بنجاح",
    "with an overall grade of": "بتقدير عام",
    "with Student ID": "برقم الطالب",
    "Awarded on:": "تاريخ المنح:",
    "examinations": "الاختبارات",
    "PASS": "ناجح",
    "FAIL": "راسب",
    "Pass": "ناجح",
    "Fail": "راسب",

    # ── Dashboard inline text ────────────────────────────────────────────────
    "Campus Filter": "تصفية حسب الحرم",
    "All campuses": "جميع الأفرع",
    "Academic Performance": "الأداء الأكاديمي",
    "Gender Split": "توزيع الجنسين",
    "Fee Collection Rate": "نسبة تحصيل الرسوم",
    "% pass rate": "نسبة النجاح",
    "this month": "هذا الشهر",
    "open classes": "فصول مفتوحة",
    "absent": "غائب",
    "overdue": "متأخر",
    "rolling 7-day rate": "معدل 7 أيام متحرك",
    "billed": "مُفوتَر",
    "of": "من",
    "students": "طالب",
    "Attendance Today": "حضور اليوم",

    # ── Portal strings ───────────────────────────────────────────────────────
    "My Children": "أبنائي",
    "School Fees": "الرسوم المدرسية",
    "No students linked to your account.": "لا يوجد طلاب مرتبطون بحسابك.",
    "Student Profile": "ملف الطالب",
    "View Details": "عرض التفاصيل",
    "Last 30 Attendance Records": "آخر 30 سجل حضور",
    "No attendance records found (portal)": "لا توجد سجلات حضور.",
    "No grades recorded yet": "لا توجد درجات مسجلة بعد",
    "No fees found": "لا توجد رسوم",
    "Announcement Detail": "تفاصيل الإعلان",
    "Published:": "تاريخ النشر:",
    "Expires:": "تنتهي:",
    "Read More": "اقرأ المزيد",
    "No announcements at this time.": "لا توجد إعلانات في الوقت الحالي.",
    "· Expires:": "· تنتهي:",
    "← Back to Announcements": "← العودة إلى الإعلانات",
    "View own schedule, grades, and assignments.": "عرض الجدول الدراسي والدرجات والواجبات.",
    "View children's attendance, fees, and notifications.": "عرض حضور الأبناء ورسومهم وإشعاراتهم.",

    # ── Python _() validation messages ─────────────────────────────────────
    "Birth date cannot be in the future.": "لا يمكن أن يكون تاريخ الميلاد في المستقبل.",
    "End date must be after start date.": "يجب أن يكون تاريخ النهاية بعد تاريخ البداية.",
    "Attendance date cannot be in the future.": "لا يمكن أن يكون تاريخ الحضور في المستقبل.",
    "Absence alert email template not found.": "لم يتم العثور على نموذج بريد التنبيه.",
    "Absence alert sent to %d guardian(s).": "تم إرسال تنبيه الغياب إلى %d ولي أمر.",
    "Maximum score must be greater than 0.": "يجب أن تكون الدرجة الكاملة أكبر من الصفر.",
    "Pass score must be between 0 and the maximum score.": "يجب أن تكون درجة النجاح بين الصفر والدرجة الكاملة.",
    "Score cannot be negative.": "لا يمكن أن تكون الدرجة سالبة.",
    "Score (%s) cannot exceed maximum score (%s).": "الدرجة (%s) لا يمكن أن تتجاوز الدرجة الكاملة (%s).",
    "Fee amount must be greater than zero.": "يجب أن يكون مبلغ الرسوم أكبر من الصفر.",
    "Cannot cancel a fee that has confirmed payments.": "لا يمكن إلغاء رسوم لها مدفوعات مؤكدة.",
    "Total payments (%.2f) would exceed the fee amount (%.2f).": "إجمالي المدفوعات (%.2f) سيتجاوز مبلغ الرسوم (%.2f).",
    "Payment amount must be greater than zero.": "يجب أن يكون مبلغ الدفع أكبر من الصفر.",
    "End time must be after start time.": "يجب أن يكون وقت الانتهاء بعد وقت البدء.",
    "Class \"%s\" has exceeded its capacity of %d students.": "تجاوز الفصل \"%s\" طاقته الاستيعابية البالغة %d طالباً.",
    "Class %s already has an active timetable (%s).": "الفصل %s لديه جدول دراسي نشط بالفعل (%s).",
    "Teacher %s is already assigned on %s - %s (Class: %s).": "المعلم %s مُعيَّن بالفعل في يوم %s - %s (الفصل: %s).",
    "No email addresses found for the selected audience.": "لم يتم العثور على عناوين بريد إلكتروني للجمهور المحدد.",
    "Announcement emailed to %d recipients.": "تم إرسال الإعلان بالبريد الإلكتروني إلى %d مستلم.",
    "An invoice already exists for this fee: %s": "توجد فاتورة بالفعل لهذا الرسم: %s",

    # ── Constraint messages ──────────────────────────────────────────────────
    "Student ID must be unique.": "يجب أن يكون رقم الطالب فريداً.",
    "Subject code must be unique.": "يجب أن يكون رمز المادة فريداً.",
    "Employee ID must be unique.": "يجب أن يكون رقم الموظف فريداً.",
    "Academic year code must be unique.": "يجب أن يكون رمز السنة الدراسية فريداً.",
    "Attendance record already exists for this student on this date.": "يوجد سجل حضور لهذا الطالب في هذا التاريخ بالفعل.",
    "Grade already exists for this student in this exam.": "توجد درجة لهذا الطالب في هذا الاختبار بالفعل.",
    "Fee type code must be unique.": "يجب أن يكون رمز نوع الرسم فريداً.",
    "Fee ID must be unique.": "يجب أن يكون رقم الرسم فريداً.",
    "Receipt number must be unique.": "يجب أن يكون رقم الإيصال فريداً.",
    "This class already has a subject at this day and period.": "يوجد بالفعل مادة لهذا الفصل في هذا اليوم والحصة.",
    "School code must be unique.": "يجب أن يكون رمز المدرسة فريداً.",

    # ── Action names ─────────────────────────────────────────────────────────
    "School Branches": "فروع المدرسة",
    "Guardians": "أولياء الأمور",
    "Subjects": "المواد الدراسية",
    "Search Announcements": "البحث عن إعلانات",

    # ── Help texts / no-content messages ────────────────────────────────────
    "Register your first student": "سجّل أول طالب",
    "Add your first guardian": "أضف ولي أمر",
    "Add your first teacher": "أضف أول معلم",
    "Create your first classroom": "أنشئ أول فصل دراسي",
    "Create the first exam": "أنشئ أول اختبار",
    "Record the first attendance entry": "سجّل أول حضور",
    "Add your first school branch or campus": "أضف أول فرع أو حرم مدرسي",
    "Additional notes...": "ملاحظات إضافية...",
    "Add specific students…": "أضف طلاباً محددين…",
    "All classes (leave empty for all)": "جميع الفصول (اتركه فارغاً للكل)",
    "e.g. 2024-2025 Term 1": "مثال: 2024-2025 الفصل الأول",

    # ── Stat button labels ───────────────────────────────────────────────────
    "Students (stat)": "الطلاب",
    "Teachers (stat)": "المعلمون",
    "Classes (stat)": "الفصول",
    "Recipients (stat)": "المستلمون",
    "Attendance (stat)": "الحضور",
    "Grades (stat)": "الدرجات",
    "Payments (stat)": "المدفوعات",
    "Invoice": "فاتورة",

    # ── Misc report / email action subjects ─────────────────────────────────
    "'Attendance Report - ' + (object.name or '')": "'تقرير الحضور - ' + (object.name or '')",
    "'Completion Certificate - ' + (object.name or '')": "'شهادة إتمام الدراسة - ' + (object.name or '')",
    "'Enrollment Certificate - ' + (object.name or '')": "'شهادة القيد - ' + (object.name or '')",
    "'Fee Statement - ' + (object.name or '')": "'كشف الرسوم - ' + (object.name or '')",
    "'Grade Report - ' + (object.name or '')": "'تقرير الدرجات - ' + (object.name or '')",
    "'Receipt - ' + (object.payment_code or '')": "'إيصال - ' + (object.payment_code or '')",
    "'Timetable - ' + (object.display_name or '')": "'الجدول الدراسي - ' + (object.display_name or '')",
    "Absence Notice: {{ object.student_id.name }} — {{ object.date }}": "إشعار غياب: {{ object.student_id.name }} — {{ object.date }}",

    # ── Mail / chatter fields ────────────────────────────────────────────────
    "Activities": "الأنشطة",
    "Action Needed": "إجراء مطلوب",
    "Activity Exception Decoration": "زخرفة استثناء النشاط",
    "Activity State": "حالة النشاط",
    "Activity Type Icon": "أيقونة نوع النشاط",
    "Website Messages": "رسائل الموقع",
    "Website communication history": "سجل تواصل الموقع",

    # ── Announcement help text / dashboard text ──────────────────────────────
    "Announcement Title": "عنوان الإعلان",
    "Announcement": "الإعلان",

    # ── Report HTML strong tags (view arch extractions) ──────────────────────
    "<strong>Academic Year:</strong>": "<strong>السنة الدراسية:</strong>",
    "<strong>Class:</strong>": "<strong>الفصل:</strong>",
    "<strong>Enrollment Date:</strong>": "<strong>تاريخ القيد:</strong>",
    "<strong>Grade Level:</strong>": "<strong>المرحلة الدراسية:</strong>",
    "<strong>Guardian Phone:</strong>": "<strong>هاتف ولي الأمر:</strong>",
    "<strong>Guardian:</strong>": "<strong>ولي الأمر:</strong>",
    "<strong>ID:</strong>": "<strong>الرقم:</strong>",
    "<strong>Name:</strong>": "<strong>الاسم:</strong>",
    "<strong>Notes:</strong>": "<strong>ملاحظات:</strong>",
    "<strong>Print Date:</strong>": "<strong>تاريخ الطباعة:</strong>",
    "<strong>Reference:</strong>": "<strong>المرجع:</strong>",
    "<strong>Status:</strong>": "<strong>الحالة:</strong>",
    "<strong>Student ID:</strong>": "<strong>رقم الطالب:</strong>",
    "<strong>Student Name:</strong>": "<strong>اسم الطالب:</strong>",
    "<strong>Student:</strong>": "<strong>الطالب:</strong>",
    "<strong>Teacher:</strong>": "<strong>المعلم:</strong>",
    "<span>School Dashboard</span>": "<span>لوحة معلومات المدرسة</span>",
    "<span class=\"badge bg-success ms-1\">Emailed</span>": "<span class=\"badge bg-success ms-1\">أُرسل</span>",
    "<span class=\"o_stat_text\">Invoice</span>": "<span class=\"o_stat_text\">فاتورة</span>",
    "<i class=\"fa fa-user-tie\" title=\"Principal\"/>": "<i class=\"fa fa-user-tie\" title=\"مدير المدرسة\"/>",

    # ── Fee description fields ────────────────────────────────────────────────
    "Regular academic term tuition fee": "رسوم دراسية منتظمة للفصل الدراسي",
    "Annual registration and enrollment fee": "رسوم التسجيل والقيد السنوية",
    "Extracurricular and school activities fee": "رسوم الأنشطة اللاصفية والمدرسية",
    "School bus and transportation fee": "رسوم حافلة المدرسة والنقل",
    "Textbooks and study materials fee": "رسوم الكتب المدرسية والمواد الدراسية",
    "Examination and assessment fee": "رسوم الاختبارات والتقييم",

    # ── State labels used in various places ──────────────────────────────────
    "State": "الحالة",
    "Term": "الفصل الدراسي",

    # ── Additional missing strings ────────────────────────────────────────────
    "Accountant": "محاسب",
    "Additional Students": "طلاب إضافيون",
    "Attachment Count": "عدد المرفقات",
    "Attendance Record": "سجل الحضور",
    "Branch Code": "رمز الفرع",
    "Bulk Parent Communication": "التواصل الجماعي مع أولياء الأمور",
    "Cannot create invoice: no guardian or partner found for student %s.": "تعذّر إنشاء الفاتورة: لم يتم العثور على ولي أمر للطالب %s.",
    "Close": "إغلاق",
    "Comments...": "تعليقات...",
    "Count": "العدد",
    "Create your first academic year": "أنشئ أول سنة دراسية",
    "Created by": "أنشئ بواسطة",
    "Created on": "أُنشئ في",
    "Details": "التفاصيل",
    "Display Name": "اسم العرض",
    "Edit Slots": "تعديل الحصص",
    "Emailed": "أُرسل",
    "Enrollment Confirmation - {{ object.name }}": "تأكيد التسجيل - {{ object.name }}",
    "Exam description, topics covered...": "وصف الاختبار والمواضيع المشمولة...",
    "Fee": "الرسم",
    "Fee Type Name": "اسم نوع الرسم",
    "Fee for student: %s | %s": "رسم للطالب: %s | %s",
    "Fees Outstanding": "الرسوم المتبقية",
    "Filter dashboard to a specific school. Leave empty to see all schools.": "تصفية لوحة المعلومات حسب مدرسة محددة. اتركه فارغاً لعرض جميع المدارس.",
    "Followers": "المتابعون",
    "Followers (Partners)": "المتابعون (الشركاء)",
    "Font awesome icon e.g. fa-tasks": "أيقونة Font Awesome مثل: fa-tasks",
    "Full access to all school data, users, and configuration.": "وصول كامل لجميع بيانات المدرسة والمستخدمين والإعدادات.",
    "Full address...": "العنوان الكامل...",
    "Grade Letter": "حرف التقدير",
    "Guardian Full Name": "اسم ولي الأمر الكامل",
    "Has Message": "يحتوي رسائل",
    "ID": "الرقم",
    "Icon": "الأيقونة",
    "Icon to indicate an exception activity.": "أيقونة للإشارة إلى نشاط استثنائي.",
    "If checked, new messages require your attention.": "إذا تم تحديده، فإن الرسائل الجديدة تستلزم انتباهك.",
    "If checked, some messages have a delivery error.": "إذا تم تحديده، فإن بعض الرسائل تحتوي على خطأ في التسليم.",
    "Internal notes...": "ملاحظات داخلية...",
    "Invoice Balance": "رصيد الفاتورة",
    "Invoice Status": "حالة الفاتورة",
    "Invoice can only be created for due or overdue fees.": "لا يمكن إنشاء الفاتورة إلا للرسوم المستحقة أو المتأخرة.",
    "Is Follower": "متابع",
    "Last Updated by": "آخر تحديث بواسطة",
    "Last Updated on": "آخر تحديث في",
    "Leave empty to target all classes": "اتركه فارغاً لاستهداف جميع الفصول",
    "Manage fees, payments, and financial reports.": "إدارة الرسوم والمدفوعات والتقارير المالية.",
    "Max": "الأقصى",
    "Message": "الرسالة",
    "Message Delivery error": "خطأ في تسليم الرسالة",
    "Message sent to %d guardians.": "تم إرسال الرسالة إلى %d ولي أمر.",
    "Messages": "الرسائل",
    "My Activity Deadline": "موعد نشاطي",
    "Name": "الاسم",
    "New": "جديد",
    "Next Activity Deadline": "موعد النشاط التالي",
    "Next Activity Summary": "ملخص النشاط التالي",
    "Next Activity Type": "نوع النشاط التالي",
    "No fees found.": "لا توجد رسوم.",
    "No grades recorded yet.": "لا توجد درجات مسجلة بعد.",
    "No guardian emails found for the selected students/classes.": "لم يتم العثور على بريد إلكتروني لأولياء الأمور للطلاب/الفصول المحددة.",
    "No income account found. Please configure your Chart of Accounts.": "لم يتم العثور على حساب الإيرادات. يرجى تكوين دليل الحسابات.",
    "No payments recorded yet": "لا توجد مدفوعات مسجلة بعد",
    "No recipients found.": "لم يتم العثور على مستلمين.",
    "Notes...": "ملاحظات...",
    "Notes…": "ملاحظات...",
    "Notify by Email": "إخطار بالبريد الإلكتروني",
    "Number of Actions": "عدد الإجراءات",
    "Number of errors": "عدد الأخطاء",
    "Number of messages requiring action": "عدد الرسائل التي تتطلب إجراءً",
    "Number of messages with delivery error": "عدد الرسائل ذات خطأ في التسليم",
    "Preview": "معاينة",
    "Recipient Count": "عدد المستلمين",
    "Recipients Found": "المستلمون الموجودون",
    "Recipients Preview": "معاينة المستلمين",
    "Record Class Attendance": "تسجيل حضور الفصل",
    "Record attendance and grades for own classes.": "تسجيل الحضور والدرجات للفصول الخاصة.",
    "Register students, manage transfers, issue files.": "تسجيل الطلاب وإدارة التحويلات وإصدار الملفات.",
    "Reset": "إعادة تعيين",
    "Responsible User": "المستخدم المسؤول",
    "Result": "النتيجة",
    "SMS Delivery error": "خطأ في تسليم الرسالة القصيرة",
    "Schedule": "الجدول",
    "School / Campus Name": "اسم المدرسة / الحرم",
    "School Branch": "فرع المدرسة",
    "School Logo": "شعار المدرسة",
    "School: Daily Overdue Fee Check": "المدرسة: التحقق اليومي من الرسوم المتأخرة",
    "School: Fee Overdue Reminder Emails": "المدرسة: رسائل تذكير الرسوم المتأخرة",
    "School: Fee Payment Reminder": "المدرسة: تذكير سداد الرسوم",
    "School: Payment Receipt": "المدرسة: إيصال الدفع",
    "School: Student Absence Alert": "المدرسة: تنبيه غياب الطالب",
    "School: Student Enrollment Confirmation": "المدرسة: تأكيد تسجيل الطالب",
    "School<br/>Seal": "ختم<br/>المدرسة",
    "Select classes…": "اختر فصولاً...",
    "Sequence": "الترتيب",
    "Student": "طالب",
    "Subject…": "المادة...",
    "Type": "النوع",
    "Wizard": "المعالج",
    "/my/fees": "/my/fees",
    "/my/students": "/my/students",
    "/web/static/img/avatars/avatar_1.png": "/web/static/img/avatars/avatar_1.png",
    "/web/static/img/avatars/avatar_10.png": "/web/static/img/avatars/avatar_10.png",
    "Type of the exception activity on record.": "نوع النشاط الاستثنائي في السجل.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Arabic translations for MULTILINE email templates
# ─────────────────────────────────────────────────────────────────────────────
EMAIL_TRANSLATIONS = {
    # Absence alert email body
    "email_template_absence_alert_body": """\n<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;" dir="rtl">\n    <div style="background-color: #e74c3c; padding: 20px; text-align: center;">\n        <h2 style="color: white; margin: 0;">إشعار غياب</h2>\n    </div>\n    <div style="padding: 20px; border: 1px solid #ddd;">\n        <p>عزيزي/عزيزتي {{ object.student_id.guardian_id.name or 'ولي الأمر' }}،</p>\n        <p>نود إعلامكم بأن <strong>{{ object.student_id.name }}</strong>\n           تم تسجيله/ها <strong style="color:#e74c3c;">غائباً/ة</strong> بتاريخ\n           <strong>{{ object.date }}</strong>.</p>\n        <table style="width:100%; border-collapse:collapse; margin:15px 0;">\n            <tr style="background:#f2f2f2;">\n                <td style="padding:8px; border:1px solid #ddd;"><strong>الطالب</strong></td>\n                <td style="padding:8px; border:1px solid #ddd;">{{ object.student_id.name }}</td>\n            </tr>\n            <tr>\n                <td style="padding:8px; border:1px solid #ddd;"><strong>رقم الطالب</strong></td>\n                <td style="padding:8px; border:1px solid #ddd;">{{ object.student_id.student_code }}</td>\n            </tr>\n            <tr style="background:#f2f2f2;">\n                <td style="padding:8px; border:1px solid #ddd;"><strong>الفصل</strong></td>\n                <td style="padding:8px; border:1px solid #ddd;">{{ object.class_id.display_name }}</td>\n            </tr>\n            <tr>\n                <td style="padding:8px; border:1px solid #ddd;"><strong>التاريخ</strong></td>\n                <td style="padding:8px; border:1px solid #ddd;">{{ object.date }}</td>\n            </tr>\n            {% if object.notes %}\n            <tr style="background:#f2f2f2;">\n                <td style="padding:8px; border:1px solid #ddd;"><strong>ملاحظات</strong></td>\n                <td style="padding:8px; border:1px solid #ddd;">{{ object.notes }}</td>\n            </tr>\n            {% endif %}\n        </table>\n        <p>إذا كان الغياب مبرراً، يرجى التواصل مع إدارة المدرسة بخطاب عذر.</p>\n        <p>مع التقدير،<br/><strong>إدارة المدرسة</strong></p>\n    </div>\n</div>\n        """,
}


# ─────────────────────────────────────────────────────────────────────────────
# Parser / generator
# ─────────────────────────────────────────────────────────────────────────────

def parse_pot(path):
    """Return list of (comment_lines, msgid_lines, is_multiline)."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    entries = []
    # Split on double-newlines that separate entries
    blocks = re.split(r"\n\n(?=#\.)", content)
    # Also handle first block (header)
    header_match = re.match(r"(.*?)\n\n(?=#\.)", content, re.DOTALL)
    header = header_match.group(1) if header_match else ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        comment_lines = []
        msgid_lines = []
        in_msgid = False
        for line in lines:
            if line.startswith("#"):
                comment_lines.append(line)
            elif line.startswith("msgid "):
                in_msgid = True
                msgid_lines.append(line)
            elif in_msgid and line.startswith('"'):
                msgid_lines.append(line)
            elif line.startswith("msgstr"):
                break

        if msgid_lines:
            entries.append((comment_lines, msgid_lines))

    return header, entries


def extract_msgid_value(msgid_lines):
    """Get the raw string value from msgid lines."""
    parts = []
    for line in msgid_lines:
        # Strip the msgid prefix and quotes
        line = line.strip()
        if line.startswith("msgid "):
            line = line[6:]
        if line.startswith('"') and line.endswith('"'):
            # Unescape
            val = line[1:-1]
            parts.append(val)
    return "".join(parts).replace("\\n", "\n").replace('\\"', '"')


def build_msgstr(msgid_value, msgid_lines):
    """Return the msgstr line(s) for a given msgid value."""
    # Check translation dict first
    translation = TRANSLATIONS.get(msgid_value, "")
    if translation:
        # Escape back
        escaped = translation.replace('"', '\\"').replace("\n", "\\n")
        return f'msgstr "{escaped}"'
    # Multiline: return empty
    return 'msgstr ""'


def generate_po(pot_path, out_path):
    header, entries = parse_pot(pot_path)

    lines_out = []

    # Write header with Arabic locale
    ar_header = """# Arabic translation of School Management System
# Copyright (C) 2026 School Management
#
msgid ""
msgstr ""
"Project-Id-Version: Odoo Server 17.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2026-06-13 00:00+0000\\n"
"PO-Revision-Date: 2026-06-13 00:00+0000\\n"
"Last-Translator: \\n"
"Language-Team: Arabic\\n"
"Language: ar_SA\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5;\\n"
"""
    lines_out.append(ar_header)

    for comment_lines, msgid_lines in entries:
        msgid_value = extract_msgid_value(msgid_lines)
        if not msgid_value:
            continue  # skip empty msgid (header)

        lines_out.append("\n")
        for c in comment_lines:
            lines_out.append(c + "\n")
        for m in msgid_lines:
            lines_out.append(m + "\n")

        translation = TRANSLATIONS.get(msgid_value, "")
        if translation:
            escaped = translation.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            lines_out.append(f'msgstr "{escaped}"\n')
        else:
            lines_out.append('msgstr ""\n')

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines_out)

    translated = sum(1 for _, ml in entries
                     if TRANSLATIONS.get(extract_msgid_value(ml), ""))
    total = len(entries)
    print(f"Written: {out_path}")
    print(f"Translated: {translated}/{total} entries ({100*translated//total}%)")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    generate_po(
        os.path.join(base, POT),
        os.path.join(base, OUT),
    )
