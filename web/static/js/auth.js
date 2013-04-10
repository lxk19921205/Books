/*
 * @author: Andriy Lin
 * @description: verification codes used in signup.html & login.html
 */

var EMAIL_PATTERN = new RegExp("^[\\S]+@[\\S]+\\.[\\S]+$");
var PWD_PATTERN = new RegExp("^.{6,30}$");

var STRINGS = {
    'email': {
        'info': "Your email address will be your user id",
        'error': "Please enter a valid email address"
    },
    'pwd': {
        'info': "Shall be 6 to 30 characters long",
        'error': "Shall be 6 to 30 characters long"
    },
    'verify': {
        'info': "Enter your password again",
        'error': "The passwords do not match"
    }
};

/**
 * render some string info onto form fields
 * called when the webpage is loaded, called only once
 */
function render_signup() {
    fields = ['email', 'pwd', 'verify'];
    for(pos in fields) {
        var name = fields[pos];
        var ele = document.getElementById(name + "_info");
        if (ele.innerHTML) {
            // generally, there shall be nothing, but when registration fails
            // (e.g. the email has been registered by somebody else),
            // then the server will render the page with some notifications here
            // just keep the words and bind a css
            ele.className = "error";
        } else {
            ele.innerHTML = STRINGS[name]['info'];
        }
    }
}


/**
 * validate the input of Email, Password, and Verify_Password in sign-up page
 * only when all of them are valid will the form be submitted
 */
function validate_signup() {
    var valid = true;

    // MUST put 'pwd' before 'verify' because validating 'verify' requires 'pwd'
    var fields = ['email', 'pwd', 'verify'];
    var values = {};
    var check_methods = {
        'email': function(email) {
            return EMAIL_PATTERN.test(email);
        },
        'pwd': function(pwd) {
            return PWD_PATTERN.test(pwd);
        },
        'verify': function(verify) {
            return verify === values['pwd'];
        }
    };

    for (pos in fields) {
        var name = fields[pos];
        values[name] = document.getElementById(name + "_field").value;
        var info_field = document.getElementById(name + "_info");

        // validating
        if (check_methods[name](values[name])) {
            info_field.className = 'correct';
            info_field.innerHTML = STRINGS[name]['info'];
        } else {
            valid = false;
            info_field.className = 'error';
            info_field.innerHTML = STRINGS[name]['error'];
        }
    }

    return valid;
}

/**
 * validate the input of Email & Password in log-in page
 */
function validate_login() {
    var valid = true;

    email = document.getElementById('email_field').value;
    pwd = document.getElementById('pwd_field').value;

    email_info = document.getElementById('email_info');
    pwd_info = document.getElementById('pwd_info');

    // email
    if (EMAIL_PATTERN.test(email)) {
        email_info.innerHTML = "";
    } else {
        valid = false;
        email_info.innerHTML = STRINGS['email']['error'];
    }

    // pwd
    if (PWD_PATTERN.test(pwd)) {
        pwd_info.innerHTML = "";
    } else {
        pwd_info.innerHTML = "";
        valid = false;
        pwd_info.innerHTML = STRINGS['pwd']['error'];
    }

    return valid;
}
