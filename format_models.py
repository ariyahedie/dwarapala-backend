def format_company(company):
  return {
    "id": company.company_id,
    "name": company.company_name,
    "email": company.company_email,
    "created_at": company.company_created_at,
    "status": company.company_account_status
  }

def format_usertype(usertype):
  return {
    "name": usertype.usertype_name
  }

def format_department(department):
  return {
    "department": department.department_name,
    "company": department.company_id
  }

def format_position(position):
  return {
    "position": position.position_name,
    "company": position.company_id
  }

def format_superadmin(superadmin):
  return {
    "id": superadmin.superadmin_id,
    "name": superadmin.superadmin_name,
    "email": superadmin.superadmin_email
  }