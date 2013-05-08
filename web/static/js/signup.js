/*
 * @author: Andriy Lin
 * for sign-up page
 */

// Andriy Books namespace
var ab = ab || {};


/**
 * Render some string info onto form fields
 * Called when the webpage is loaded, called only once
 */
ab.init_signup = function() {
    fields = ['email', 'pwd', 'verify'];
    for(var idx in fields) {
    	var name = fields[idx];
    	var ele = document.getElementById(name + '_info');
    	if (ele.innerHTML) {
    		/*
    		 * If there is sth., this web page comes from server after validating the sign-up data
    		 * Then it would be an error message
    		 */
    		 ele.className = "error";
    	} else {
    		/*
    		 * If there is nothing, it is just an empty form waiting for input, show hints
    		 */
    		 ele.innerHTML = ab.STRINGS['signup'][name]['info'];
    	}
    }
}


/**
 * Validate the input of Email, Password, and Verify_Password in sign-up page
 * Only when all of them are valid will the form be submitted
 */
ab.validate_signup = function() {
    var valid = true;

    // for email, just ensure there is sth. is enough, browser will help us validate it
    var email_field = document.getElementById('email_field');
    if (!email_field.value) {
    	email_field.focus();
    	return false;
    }

    // password
    var pwd_field = document.getElementById('pwd_field');
    var pwd_info_field = document.getElementById('pwd_info');
    if (!ab.PWD_PATTERN.test(pwd_field.value)) {
    	pwd_info_field.className = "error";
    	pwd_info_field.innerHTML = ab.STRINGS['signup']['pwd']['error'];

    	pwd_field.focus();
    	return false;
    } else {
	    pwd_info_field.className = "info";
	    pwd_info_field.innerHTML = ab.STRINGS['signup']['pwd']['info'];
    }

    // verify
    var verify_field = document.getElementById('verify_field');
    var verify_info_field = document.getElementById('verify_info');
    if (verify_field.value !== pwd_field.value) {
    	verify_info_field.className = "error";
    	verify_info_field.innerHTML = ab.STRINGS['signup']['verify']['error'];

    	verify_field.focus();
    	return false;
    } else {
    	verify_info_field.className = "info";
    	verify_info_field.innerHTML = ab.STRINGS['signup']['verify']['info'];
    }

    return true;
}
