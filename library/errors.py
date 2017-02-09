api_errors = {
    # file upload errors
    "API_UNAUTHORIZED": {
        "code": 4000,
        "msg": "Unauthorized."
    },
    "JOBS_NO_ATTACHMENT": {
        "code": 5000,
        "msg": "/jobs/create was called without a file or text body attachment."
    },
    "JOBS_BAD_DESTINATION": {
        "code": 5001,
        "msg": "An invalid destination phone number was passed for this job."
    },
    "JOBS_BAD_COVER": {
        "code": 5002,
        "msg": "An invalid value passed for cover."
    },
    "JOBS_BAD_FILENAME": {
        "code": 5003,
        "msg": "The specified filename was invalid."
    },
    "JOBS_BAD_SEND_AUTHORIZED": {
        "code": 5004,
        "msg": "Invalid value passed for send_authorized."
    },
    "JOBS_BAD_COVER_NAME": {
        "code": 5005,
        "msg": "Invalid cover sheet name field (Max 64 characters).",
        "field": "cover_name"
    },
    "JOBS_BAD_COVER_ADDRESS": {
        "code": 5006,
        "msg": "Invalid cover sheet address field (Max 128 characters).",
        "field": "cover_address"
    },
    "JOBS_BAD_COVER_CITY": {
        "code": 5007,
        "msg": "Invalid cover sheet city field (Max 64 characters).",
        "field": "cover_city"
    },
    "JOBS_BAD_COVER_STATE": {
        "code": 5008,
        "msg": "Invalid cover sheet state field (Max 64 characters).",
        "field": "cover_state"
    },
    "JOBS_BAD_COVER_ZIP": {
        "code": 5009,
        "msg": "Invalid cover sheet zip field (Max 64 characters).",
        "field": "cover_zip"
    },
    "JOBS_BAD_COVER_COUNTRY": {
        "code": 5010,
        "msg": "Invalid cover sheet country field (Max 64 characters).",
        "field": "cover_country"
    },
    "JOBS_BAD_COVER_PHONE": {
        "code": 5011,
        "msg": "Invalid cover sheet phone number field (Max 64 characters).",
        "field": "cover_phone"
    },
    "JOBS_BAD_COVER_EMAIL": {
        "code": 5012,
        "msg": "Invalid cover sheet email field (Max 128 characters).",
        "field": "cover_email"
    },
    "JOBS_BAD_COVER_COMPANY": {
        "code": 5013,
        "msg": "Invalid cover sheet company field (Max 128 characters).",
        "field": "cover_company"
    },
    "JOBS_BAD_COVER_TO_NAME": {
        "code": 5014,
        "msg": "Invalid cover sheet to name field (Max 64 characters).",
        "field": "cover_to_name"
    },
    "JOBS_BAD_COVER_CC": {
        "code": 5015,
        "msg": "Invalid cover sheet cc field (Max 64 characters).",
        "field": "cover_cc"
    },
    "JOBS_BAD_COVER_SUBJECT": {
        "code": 5016,
        "msg": "Invalid cover sheet subject field (Max 64 characters).",
        "field": "cover_subject"
    },
    "JOBS_BAD_COVER_STATUS": {
        "code": 5017,
        "msg": "Invalid cover sheet status field (Max 64 characters).",
        "field": "cover_status"
    },
    "JOBS_BAD_CALLBACK_URL": {
        "code": 5018,
        "msg": "Invalid callback_url field (Max 255 characters).",
        "field": "callback_url"
    },
    "JOBS_MISSING_DESTINATION": {
        "code": 5019,
        "msg": "Could not start the job because no destination was passed."
    },
    "JOBS_NOT_READY": {
        "code": 5020,
        "msg": "This job has begun processing, so you can't change it anymore."
    },
    "JOBS_BAD_PAGINATION_VALUE": {
        "code": 5021,
        "msg": "You sent an unacceptable page parameter."
    },
    "JOBS_NOT_RESTARTABLE": {
        "code": 5022,
        "msg": "The specified job is not failed and cannot be restarted."
    },
    "JOBS_DATA_DELETED": {
        "code": 5023,
        "msg": "The data for this job has been deleted from the server. Please recreate."
    },
    "JOBS_CANNOT_DELETE_NOW": {
        "code": 5024,
        "msg": "The job is being processed and cannot be deleted now."
    },
    "ACCOUNTS_MISSING_EMAIL": {
        "code": 6000,
        "msg": "Please enter an email address.",
        "field": "email"
    },
    "ACCOUNTS_BAD_EMAIL": {
        "code": 6001,
        "msg": "Please enter a valid email address.",
        "field": "email"
    },
    "ACCOUNTS_MISSING_PASSWORD": {
        "code": 6002,
        "msg": "Please enter a password.",
        "field": "password"
    },
    "ACCOUNTS_CREATE_FAIL": {
        "code": 6003,
        "msg": "Could not create that account. Perhaps it already exists?",
        "field": "email"
    },
    "ACCOUNTS_LOGIN_ERROR": {
        "code": 6004,
        "msg": "Could not find an account with that username and password."
    },
    "ACCOUNTS_PAYMENT_FAIL": {
        "code": 6005,
        "msg": "Could not process payment."
    },
    "ACCOUNTS_STORED_PAYMENT_FAIL": {
        "code": 6006,
        "msg": "Could not process stored payment info."
    },
    "ACCOUNTS_BAD_FIRST_NAME": {
        "code": 6007,
        "msg": "First name was too long. Max 255 characters.",
        "field": "first_name"
    },
    "ACCOUNTS_BAD_LAST_NAME": {
        "code": 6008,
        "msg": "Last name was too long. Max 255 characters.",
        "field": "last_name"
    },
    "ACCOUNTS_BAD_ADDRESS": {
        "code": 6009,
        "msg": "Address was too long. Max 255 characters.",
        "field": "address"
    },
    "ACCOUNTS_BAD_ADDRESS2": {
        "code": 6010,
        "msg": "Address (second field) was too long. Max 255 characters.",
        "field": "address2"
    },
    "ACCOUNTS_BAD_CITY": {
        "code": 6011,
        "msg": "City was too long. Max 255 characters.",
        "field": "city"
    },
    "ACCOUNTS_BAD_STATE": {
        "code": 6012,
        "msg": "Please enter a valid state..",
        "field": "state"
    },
    "ACCOUNTS_BAD_ZIP": {
        "code": 6013,
        "msg": "Please enter a valid zip code.",
        "field": "zip"
    },
    "ACCOUNTS_BAD_REQUEST": {
        "code": 6014,
        "msg": "WTF."
    },
    "ACCOUNTS_EMAIL_TAKEN": {
        "code": 6015,
        "msg": "The email address you entered is not available.",
        "field": "email"
    },
    "ACCOUNTS_INVALID_OLD_PASSWORD": {
        "code": 6016,
        "msg": "The old password you provided was not correct.",
        "field": "old_password"
    },
    "ACCOUNTS_INVALID_RESET_HASH": {
        "code": 6017,
        "msg": "The reset hash was not valid. Perhaps the link expired?",
        "field": "reset_hash"
    },
    "INCOMING_INSUFFICIENT_CREDIT": {
        "code": 6018,
        "msg": "No funds were available in the account to provision the fax number."
    },
    "INCOMING_CARD_DECLINED": {
        "code": 6019,
        "msg": "The account's stored credit information didn't work."
    },
    "INCOMING_FAILED_TO_PROVISION": {
        "code": 6020,
        "msg": "INTERNAL ERROR. Unable to provision that phone number."
    },
    "INCOMING_BOGUS_AREA_CODE": {
        "code": 6021,
        "msg": "The area code you chose is invalid or has no numbers at this time."
    },
    "INCOMING_NUMBER_EXISTS": {
        "code": 6022,
        "msg": "You already have an incoming number set up for your account."
    },
    "INCOMING_CANNOT_REMOVE": {
        "code": 6023,
        "msg": "There was no incoming number associated with this account to remove."
    },
    "INCOMING_FAILED_TO_DEPROVISION": {
        "code": 6024,
        "msg": "An error occurred while deprovisioning your number. Please contact support."
    },
    "INCOMING_BAD_PAGINATION_VALUE": {
        "code": 6025,
        "msg": "You sent an unacceptable page parameter."
    },
    "ADMIN_BAD_ADMIN_TOKEN": {
        "code": 7000,
        "msg": "The specified admin token was invalid."
    },
}
worker_errors = {
    "JOBS_UPLOAD_S3_FAIL": {
        "code": 501,
        "status": "internal_error",
        "msg": "Upload of file to Amazon S3 failed."
    },
    "JOBS_CONNECT_S3_FAIL": {
        "code": 502,
        "status": "internal_error",
        "msg": "Could not connect to Amazon S3."
    },
    "JOBS_LOCAL_SAVE_FAIL": {
        "code": 503,
        "status": "internal_error",
        "msg": "Could not store file locally. Disk full? Permissions?"
    },
    "JOBS_IMG_CONVERT_FAIL": {
        "code": 504,
        "status": "processing_error",
        "msg": "Could not process the attached file. Was it a valid image?"
    },
    "JOBS_CREATE_DIR_FAIL": {
        "code": 505,
        "status": "internal_error",
        "msg": "Could not create directory for file uploads."
    },
    # "JOBS_TOUCH_HACK_FAIL": {
    #     "code": 506,
    #     "status": "internal_error",
    #     "msg": "Could not run convert.sh to initiate PDF conversion."
    # },
    "JOBS_PDF_CONVERT_FAIL": {
        "code": 507,
        "status": "internal_error",
        "msg": "PDF conversion failed. FFFFFFFUUUUUUUUUUUU"
    },
    "JOBS_COVER_MAIN_FAIL": {
        "code": 508,
        "status": "internal_error",
        "msg": "The main cover generation phase failed (overlaying text on PDF)"
    },
    "JOBS_COVER_COMPANY_FAIL": {
        "code": 509,
        "status": "internal_error",
        "msg": "Could not generate image containing the coversheet company text"
    },
    "JOBS_COVER_OVERLAY_FAIL": {
        "code": 510,
        "status": "internal_error",
        "msg": "Could not overlay generated text over main cover image"
    },
    "JOBS_COVER_COMMENTS_FAIL": {
        "code": 511,
        "status": "internal_error",
        "msg": "Could not generate image containting the coversheet comments"
    },
    "JOBS_COVER_TIFF_FAIL": {
        "code": 512,
        "status": "internal_error",
        "msg": "Could not convert the generated coversheet .png to G3 .tiff"
    },
    "JOBS_INSUFFICIENT_CREDIT": {
        "code": 513,
        "status": "insufficient_credit",
        "msg": "No funds were available in the account to process this job."
    },
    "JOBS_DOWNLOAD_S3_FAIL": {
        "code": 514,
        "status": "internal_error",
        "msg": "Could not download image file from Amazon S3."
    },
    "JOBS_TRANSMIT_FAIL": {
        "code": 515,
        "status": "transmit_failure",
        "msg": ("Could not transmit the fax. Please try again and contact "
                "support if the problem persists.")
    },
    "JOBS_TRANSMIT_NO_ANSWER": {
        "code": 516,
        "status": "no_answer",
        "msg": ("The number you dialed didn't answer or was not a fax machine. "
                "Please try again.")
    },
    "JOBS_TRANSMIT_BUSY": {
        "code": 517,
        "status": "busy",
        "msg": "The number you dialed was busy. Please try again later."
    },
    "JOBS_UNSUPPORTED_FORMAT": {
        "code": 518,
        "status": "unsupported_format",
        "msg": "The attached file was not of a supported format."
    },
    "JOBS_CARD_DECLINED": {
        "code": 520,
        "status": "card_declined",
        "msg": "The account's stored credit information didn't work."
    },
    "JOBS_NO_ATTACHMENT_FOUND": {
        "code": 521,
        "status": "internal_error",
        "msg": "There was no body and no filename attached to this job."
    },
    "JOBS_TXT_CONVERT_FAIL": {
        "code": 522,
        "status": "internal_error",
        "msg": "Could not convert the attached TXT file to Postscript."
    },
    "JOBS_FAIL_DATA_DELETED": {
        "code": 523,
        "status": "gone",
        "msg": "The data for this job has been deleted from the server."
    },
    "JOBS_CANNOT_SEND_NOW": {
        "code": 524,
        "status": "not_ready",
        "msg": "The job is not ready for sending."
    },
    "JOBS_NO_SERVEOFFICE2PDF": {
        "code": 525,
        "status": "processing_error",
        "msg": "No suitable converter specified for exporting Office to PDF."
    },
    "JOBS_PHAXIO_TRANSMIT_FAIL": {
        "code": 526,
        "status": "api_Error",
        "msg": "Could not transmit the fax to our telecommunications provider."
    },
    "JOBS_PHAXIO_BAD_NUMBER": {
        "code": 527,
        "status": "api_Error",
        "msg": "The given fax number was not valid."
    },
}

def api_error(ref):
    data = api_errors.get(ref, {"code": -1, "msg": "Unknown error."});
    data["error"] = True
    data["ref"] = ref
    return data

def worker_error(ref):
    data = worker_errors.get(ref, {
        "code": 500,
        "status": "internal_error",
        "msg": "Unknown error."
    });
    data["error"] = True
    data["ref"] = ref
    return data

class ValidationError(Exception):
    def __init__(self, arg):
        self.ref = arg