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
    "id": department.department_id,
    "name": department.department_name,
    "company": department.company_id
  }

def format_position(position):
  return {
    "id": position.position_id,
    "name": position.position_name,
    "company": position.company_id
  }

def format_superadmin(superadmin):
  return {
    "id": superadmin.superadmin_id,
    "name": superadmin.superadmin_name,
    "email": superadmin.superadmin_email
  }

def format_member(member):
  return {
    "id": member.member_id,
    "name": member.member_name,
    "email": member.member_email,
    "created_at": member.member_created_at,
    "company": member.company_id,
    "position": member.position_id,
    "department": member.department_id,
    "images": member.member_images,
    "usertype": member.usertype_id
  }

def format_log(log):
  return {
    "id": log.log_id,
    "member_id": log.member_id,
    "time": log.log_time
  }