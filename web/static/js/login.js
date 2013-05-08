/*
 * @author: Andriy Lin
 * for log-in page
 */

// Andriy Books namespace
var ab = ab || {};


/**
 * Validate the input of Email & Password in log-in page
 * Just to ensure they are not empty
 * The email's validity will be checked by browser automatically
 */
ab.validate_login = function() {
    var valid = true;

    // email
    email_field = document.getElementById('email_field');
    if (!email_field.value) {
    	email_field.focus();
    	return false;
    }

    // password
    pwd_field = document.getElementById('pwd_field');
    if (!pwd_field.value) {
    	pwd_field.focus();
    	return false;
    }

    return true;
}
