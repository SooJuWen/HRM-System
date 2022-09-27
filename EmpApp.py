from crypt import methods
from unittest import result
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from datetime import date
from datetime import datetime
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Home.html')

@app.route("/aboutus", methods=['GET'])
def about():
    return render_template('AboutUs.html')

@app.route("/homePage", methods=['GET'])
def HomePage():
    return render_template('Home.html')


@app.route("/addEmployee", methods=['GET'])
def AddEmployeePage():
    return render_template('AddEmp.html')

@app.route("/manageEmployee", methods=['GET'])
def ManageEmployeePage():
    return render_template('ManageEmp.html')

@app.route("/addEmp", methods=['POST'])
def AddEmployee():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_employee_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    insert_payroll_sql = "INSERT INTO payroll VALUES (%s, %s, %s, %s, %s)"
    insert_attendance_sql = "INSERT INTO attendance VALUES (%s, %s, %s)"
    insert_performance_sql = "INSERT INTO performance VALUES (%s, %s, %s, %s, %s, %s)"

    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_employee_sql, (emp_id, first_name, last_name, pri_skill, location))
        cursor.execute(insert_payroll_sql, (emp_id, 0, 0, 0, 0))
        cursor.execute(insert_attendance_sql, (emp_id, -1, ' --- '))
        cursor.execute(insert_performance_sql, (emp_id, 0, 0, 0, 0, 0.0))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmp.html')

@app.route("/retrieveEmp", methods=['GET'])
def RetrieveEmployee():
    emp_id = request.args['emp_id']

    get_fn_sql = "SELECT first_name FROM employee WHERE emp_id= " + emp_id
    get_ln_sql = "SELECT last_name FROM employee WHERE emp_id= " + emp_id
    get_ski_sql = "SELECT pri_skill FROM employee WHERE emp_id= " + emp_id
    get_loc_sql = "SELECT location FROM employee WHERE emp_id= " + emp_id
    
    cursor1 = db_conn.cursor()
    cursor2 = db_conn.cursor()
    cursor3 = db_conn.cursor()
    cursor4 = db_conn.cursor()

    db_conn.commit()

    if emp_id != "":
        cursor1.execute(get_fn_sql)
        cursor2.execute(get_ln_sql)
        cursor3.execute(get_ski_sql)
        cursor4.execute(get_loc_sql)

        if cursor1.rowcount != 0:
            first_name = str(cursor1.fetchone()[0])
            last_name = str(cursor2.fetchone()[0])
            pri_skill = str(cursor3.fetchone()[0])
            location = str(cursor4.fetchone()[0])

            cursor1.close()
            cursor2.close()
            cursor3.close()
            cursor4.close()

            return render_template('ManageEmp.html', id=emp_id, fname=first_name, lname=last_name, pskill=pri_skill, loc=location)

        else:
            return render_template('ManageEmp.html')

@app.route("/updateEmp", methods=['POST'])
def UpdateEmployee():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']

    if (first_name != "" and last_name != "" and pri_skill != "" and location != ""):
        update_sql = "UPDATE employee SET first_name = %s, last_name = %s, pri_skill = %s, location = %s WHERE emp_id = %s"
        cursor = db_conn.cursor()

        cursor.execute(update_sql, (first_name, last_name, pri_skill, location, emp_id))
        db_conn.commit()
        cursor.close()
    return render_template("ManageEmp.html")

@app.route("/deleteEmp", methods=['POST'])
def DeleteEmployee():
    emp_id = request.form['emp_id']

    if (emp_id != ""):
        delete_sql_1 = "DELETE FROM employee WHERE emp_id=%s"
        delete_sql_2 = "DELETE FROM attendance WHERE emp_id=%s"
        delete_sql_3 = "DELETE FROM payroll WHERE emp_id=%s"
        delete_sql_4 = "DELETE FROM performance WHERE emp_id=%s"
        cursor1 = db_conn.cursor()
        cursor2 = db_conn.cursor()
        cursor3 = db_conn.cursor()
        cursor4 = db_conn.cursor()

        cursor1.execute(delete_sql_1, (emp_id))
        cursor2.execute(delete_sql_2, (emp_id))
        cursor3.execute(delete_sql_3, (emp_id))
        cursor4.execute(delete_sql_4, (emp_id))

        db_conn.commit()
        cursor1.close()
        cursor2.close()
        cursor3.close()
        cursor4.close()
    return render_template("ManageEmp.html")

@app.route("/payrollPage", methods=['GET'])
def PayrollPage():
    return render_template('PayrollPage.html')

@app.route("/employeePage", methods=['GET'])
def EmployeePage():
    return render_template('EmployeePage.html')

@app.route("/changePage", methods=['GET'])
def EditPayrollPage():
    return render_template('EditPayroll.html')

@app.route("/changeEditPrf", methods=['GET'])
def UpdatePerformancePage():
    return render_template('UpdateEmpPrf.html')

@app.route("/changeViewPrf", methods=['GET'])
def ViewPerformancePage():
    return render_template('ViewEmpPrf.html')

@app.route("/getEmpName", methods=['GET'])
def GetEmpName():
    emp_id = request.args['emp_id']

    get_fn_sql = "SELECT first_name FROM employee WHERE emp_id" + " = " + emp_id
    get_ln_sql = "SELECT last_name FROM employee WHERE emp_id" + " = " + emp_id
    get_sal_sql = "SELECT salary FROM payroll WHERE emp_id" + " = " + emp_id        
    get_alw_sql = "SELECT allowance FROM payroll WHERE emp_id" + " = " + emp_id
    get_ded_sql = "SELECT deduction FROM payroll WHERE emp_id" + " = " + emp_id
    get_net_sql = "SELECT net_amount FROM payroll WHERE emp_id" + " = " + emp_id
    
    cursor1 = db_conn.cursor()
    cursor2 = db_conn.cursor()
    cursor3 = db_conn.cursor()
    cursor4 = db_conn.cursor()
    cursor5 = db_conn.cursor()
    cursor6 = db_conn.cursor()

    db_conn.commit()

    if emp_id != "":
        cursor1.execute(get_fn_sql)
        cursor2.execute(get_ln_sql)
        cursor3.execute(get_sal_sql)
        cursor4.execute(get_alw_sql)
        cursor5.execute(get_ded_sql)
        cursor6.execute(get_net_sql)

        if cursor1.rowcount != 0:
            first_name = str(cursor1.fetchone()[0])
            last_name = str(cursor2.fetchone()[0])
            salaryFloat = float(cursor3.fetchone()[0])
            allowanceFloat = float(cursor4.fetchone()[0])
            deductionFloat = float(cursor5.fetchone()[0])
            netAmountFloat = float(cursor6.fetchone()[0])
            salary = "{:.2f}".format(salaryFloat)
            allowance = "{:.2f}".format(allowanceFloat)
            deduction = "{:.2f}".format(deductionFloat)
            netAmount = "{:.2f}".format(netAmountFloat)

            cursor1.close()
            cursor2.close()
            cursor3.close()
            cursor4.close()
            cursor5.close()
            cursor6.close()

            return render_template('EditPayroll.html', id=emp_id, fname=first_name, lname=last_name, sal=salary, alw=allowance, ded=deduction, netA=netAmount)

        else:
            return render_template('EditPayroll.html')
        
@app.route("/payroll", methods=["POST"])
def UpdatePayroll():
    emp_id = request.form['emp_id']
    salaryFloat = float(request.form['salary'])
    allowanceFloat = float(request.form['allowance'])
    deductionFloat = float(request.form['deduction'])

    netAmountFloat = salaryFloat + allowanceFloat - deductionFloat

    salary = "{:.2f}".format(salaryFloat)
    allowance = "{:.2f}".format(allowanceFloat)
    deduction = "{:.2f}".format(deductionFloat)
    netAmount = "{:.2f}".format(netAmountFloat)

    update_sql = "UPDATE payroll SET salary = " + salary + ", allowance = " + allowance + ", deduction = " + deduction + ", net_amount = " + netAmount + " WHERE emp_id = " + emp_id

    cursor = db_conn.cursor()
    db_conn.commit()

    if(emp_id != ""):
        cursor.execute(update_sql)

    cursor.close()

    return render_template('EditPayroll.html')

@app.route("/getPayrollList", methods=["GET"])
def payrollList():
    select_sql = "SELECT employee.emp_id, employee.first_name, employee.last_name, payroll.salary, payroll.allowance, payroll.deduction, payroll.net_amount FROM employee, payroll WHERE employee.emp_id = payroll.emp_id"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    db_conn.commit()
    result = cursor.fetchall()

    arr = []
    for col in range(len(result)):
        arr.append([])
        arr[col].append(col + 1)
        arr[col].append(result[col][0])
        arr[col].append(result[col][1] + " " + result[col][2])
        salaryFloat = result[col][3]
        allowanceFloat = result[col][4]
        deductionFloat = result[col][5]
        netAmountFloat = result[col][6]
        arr[col].append("{:.2f}".format(salaryFloat))
        arr[col].append("{:.2f}".format(allowanceFloat))
        arr[col].append("{:.2f}".format(deductionFloat))
        arr[col].append("{:.2f}".format(netAmountFloat))

    cursor.close()

    return render_template("PayrollList.html", content=arr)

@app.route("/getEmpAtt", methods=['GET'])
def GetEmpAtt():
    emp_id = request.args['emp_id']

    get_fn_sql = "SELECT first_name FROM employee WHERE emp_id= " + emp_id
    get_ln_sql = "SELECT last_name FROM employee WHERE emp_id= " + emp_id
    get_stat_sql = "SELECT status FROM attendance WHERE emp_id= " + emp_id

    cursor1 = db_conn.cursor()
    cursor2 = db_conn.cursor()
    cursor3 = db_conn.cursor()
    db_conn.commit()

    if emp_id != "":
        cursor1.execute(get_fn_sql)
        cursor2.execute(get_ln_sql)
        cursor3.execute(get_stat_sql)
 
        first_name = str(cursor1.fetchone()[0])
        last_name = str(cursor2.fetchone()[0])
        status = str(cursor3.fetchone()[0])

    cursor1.close()
    cursor2.close()
    cursor3.close()

    return render_template('ManageAttendance.html', id=emp_id, fname=first_name, lname=last_name, stat=status)

@app.route("/attend", methods=['GET'])
def attendance():
    select_sql = "SELECT e.emp_id, e.first_name, e.last_name, a.date_modified, a.status FROM employee e, attendance a WHERE e.emp_id = a.emp_id"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    db_conn.commit()
    result = cursor.fetchall()

    arr = []
    for col in range(len(result)):
        arr.append([])
        arr[col].append(str(result[col][1]) + " " + str(result[col][2]))
        arr[col].append(result[col][0])
        arr[col].append(result[col][3])
        arr[col].append(result[col][4])

    cursor.close()
 
    return render_template("Attendance.html", content=arr)

@app.route("/manageAtt", methods=['GET', 'POST'])
def manageAttendance():
    return render_template("ManageAttendance.html")

@app.route("/updateAtt", methods=['POST'])
def updateAttendance():
    emp_id = request.form.get('emp_id')
    emp_image_file = request.files['emp_image_file']
    attendance = request.form['attendance']

    update_sql = "UPDATE attendance SET status = %s, date_modified = %s WHERE emp_id = %s"
    cursor = db_conn.cursor()

    if (attendance == "Present"):
        status = 1
    elif (attendance == "Absent"):
        status = 0
    elif (attendance == "Leave"):
        status = -2
    else:
        status = -1

    today = date.today()
    now = datetime.now()
    # dd/mm/YY
    d = today.strftime("%d/%m/%Y")
    t = now.strftime("%H:%M:%S")
    modified_time = t + ", " + d

    try:

        if (emp_image_file.filename != "" and status == -2):
            emp_leave_evidence_in_s3 = "emp-id-" + str(emp_id) + "_leave_evidence"
            s3 = boto3.resource('s3')

            try:
                s3.Bucket(custombucket).put_object(Key=emp_leave_evidence_in_s3, Body=emp_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_leave_evidence_in_s3)

            except Exception as e:
                return str(e)

            cursor.execute(update_sql, (status, modified_time, emp_id))
            db_conn.commit()    
        
        else:
            if (status == 0 or status == 1):
                cursor.execute(update_sql, (status, modified_time, emp_id))
                db_conn.commit() 

    finally:
        cursor.close()

    return render_template("ManageAttendance.html")

@app.route("/removeLeave", methods=['POST'])
def removeLeaveEvidence():
    emp_id = request.form.get('emp_id')

    update_sql = "UPDATE attendance SET status = %s, date_modified = %s WHERE emp_id = %s"
    cursor = db_conn.cursor()

    today = date.today()
    now = datetime.now()
    # dd/mm/YY
    d = today.strftime("%d/%m/%Y")
    t = now.strftime("%H:%M:%S")
    modified_time = t + ", " + d

    cursor.execute(update_sql, ("-1", modified_time, emp_id))
    db_conn.commit()
    cursor.close()

    try:
        emp_leave_evidence_in_s3 = "emp-id-" + str(emp_id) + "_leave_evidence"
        s3 = boto3.resource('s3')
        s3.Object(custombucket, emp_leave_evidence_in_s3).delete()
    except Exception as e:
            return str(e)

    return render_template("ManageAttendance.html")

@app.route("/performance", methods=["POST"])
def UpdatePerformance():
    emp_id = request.form['emp_id']
    prf_progressing = int(request.form['prf_progressing'])
    prf_completed = int(request.form['prf_completed'])
    prf_overdue = int(request.form['prf_overdue'])
    prf_delayed = int(request.form['prf_delayed'])

    prf_overall = ((((prf_completed * 3) - ((prf_overdue * 1) + (prf_delayed * 2))) / (prf_completed * 3)) * 100)

    progressing = str(prf_progressing)
    completed = str(prf_completed)
    overdue = str(prf_overdue)
    delayed = str(prf_delayed)
    overall = "{:.0f}".format(prf_overall)

    update_prf_sql = "UPDATE performance SET prf_progressing = " + progressing + ", prf_completed = " + completed + ", prf_overdue = " + overdue + ", prf_delayed = " + delayed + ", prf_overall = " + overall + " WHERE emp_id = " + emp_id

    cursor = db_conn.cursor()
    db_conn.commit()

    if(emp_id != ""):
        cursor.execute(update_prf_sql)

    cursor.close()

    return render_template('UpdateEmpPrf.html')

@app.route("/getPerformanceList", methods=["GET"])
def performanceList():
    select_sql = "SELECT employee.emp_id, employee.first_name, employee.last_name, performance.prf_progressing, performance.prf_completed, performance.prf_overdue, performance.prf_delayed, performance.prf_overall FROM employee, performance WHERE employee.emp_id = performance.emp_id"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    db_conn.commit()
    result = cursor.fetchall()

    arr = []
    for col in range(len(result)):
        arr.append([])
        arr[col].append(col + 1)
        arr[col].append(result[col][0])
        arr[col].append(result[col][1] + " " + result[col][2])
        arr[col].append(result[col][3])
        arr[col].append(result[col][4])
        arr[col].append(result[col][5])
        arr[col].append(result[col][6])
        arr[col].append("{:.0f}".format(result[col][7]) + " %")

    cursor.close()

    return render_template("ViewEmpPrf.html", content=arr)

@app.route("/checkEmp", methods=['GET'])
def CheckEmp():
    emp_id = request.args['emp_id']
    
    get_fname_sql = "SELECT first_name FROM employee WHERE emp_id" + " = " + emp_id
    get_lname_sql = "SELECT last_name FROM employee WHERE emp_id" + " = " + emp_id
    get_pgr_sql = "SELECT prf_progressing FROM performance WHERE emp_id" + " = " + emp_id        
    get_cmp_sql = "SELECT prf_completed FROM performance WHERE emp_id" + " = " + emp_id
    get_ovd_sql = "SELECT prf_overdue FROM performance WHERE emp_id" + " = " + emp_id
    get_dly_sql = "SELECT prf_delayed FROM performance WHERE emp_id" + " = " + emp_id
    get_prf_sql = "SELECT prf_overall FROM performance WHERE emp_id" + " = " + emp_id
    
    cursor1 = db_conn.cursor()
    cursor2 = db_conn.cursor()
    cursor3 = db_conn.cursor()
    cursor4 = db_conn.cursor()
    cursor5 = db_conn.cursor()
    cursor6 = db_conn.cursor()
    cursor7 = db_conn.cursor()

    db_conn.commit()
    
    if emp_id != "":
        cursor1.execute(get_fname_sql)
        cursor2.execute(get_lname_sql)
        cursor3.execute(get_pgr_sql)
        cursor4.execute(get_cmp_sql)
        cursor5.execute(get_ovd_sql)
        cursor6.execute(get_dly_sql)
        cursor7.execute(get_prf_sql)

        if cursor1.rowcount != 0:
            first_name = str(cursor1.fetchone()[0])
            last_name = str(cursor2.fetchone()[0])
            prf_progressing = int(cursor3.fetchone()[0])
            prf_completed = int(cursor4.fetchone()[0])
            prf_overdue = int(cursor5.fetchone()[0])
            prf_delayed = int(cursor6.fetchone()[0])
            prf_overall = "{:.0f}".format(float(cursor7.fetchone()[0]))
            
            cursor1.close()
            cursor2.close()
            cursor3.close()
            cursor4.close()
            cursor5.close()
            cursor6.close()
            cursor7.close()
            
            return render_template('UpdateEmpPrf.html', id = emp_id, fname = first_name, lname = last_name, pgr = prf_progressing, cmp = prf_completed, ovd = prf_overdue, dly = prf_delayed, prf = prf_overall)
            
    else:
            return render_template('UpdateEmpPrf.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
