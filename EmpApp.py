from crypt import methods
from unittest import result
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
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


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/homePage", methods=['GET'])
def HomePage():
    return render_template('Home.html')


@app.route("/addEmployee", methods=['GET'])
def AddEmployeePage():
    return render_template('AddEmp.html')


@app.route("/payrollPage", methods=['GET'])
def PayrollPage():
    return render_template('PayrollPage.html')


@app.route("/changePage", methods=['GET'])
def EditPayrollPage():
    return render_template('EditPayroll.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_employee_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    insert_payroll_sql = "INSERT INTO payroll VALUES (%s, %s, %s, %s, %s)"

    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_employee_sql, (emp_id, first_name, last_name, pri_skill, location))
        cursor.execute(insert_payroll_sql, (emp_id, 0, 0, 0, 0))
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
    return render_template('AddEmpOutput.html', name=emp_name)


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
        arr[col].append(result[col][1] + result[col][2])
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
