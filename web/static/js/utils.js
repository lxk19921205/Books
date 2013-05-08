/*
 * @author: Andriy Lin
 *
 * All functions and variables that are shared by different pages are put here.
 * This will be the first loaded js file in all pages.
 */

// Andriy Books namespace
var ab = ab || {};


// the pattern for validating email & password
ab.EMAIL_PATTERN = new RegExp("^[\\S]+@[\\S]+\\.[\\S]+$");
ab.PWD_PATTERN = new RegExp("^.{6,30}$");


// literals used in js validation
ab.STRINGS = {
	'login': {
		'email': "Please enter your email",
		'pwd': "Please enter your password"
	},

	'signup': {
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
	}
};
