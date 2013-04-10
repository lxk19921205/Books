/*
 * @author: Andriy Lin
 * @description: verification codes used in signup.html
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

/*
 * render some string info onto form fields
 */
function render() {
    fields = ['email', 'pwd', 'verify'];
    for(pos in fields) {
        var name = fields[pos];
        document.getElementById(name + "_info").innerHTML = STRINGS[name]['info'];
    }
}


/*
 * validate the input of Email, Password, and Verify_Password
 * only when all of them are valid will the form be submitted
 */
function validate() {
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
            return verify == values['verify'];
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

