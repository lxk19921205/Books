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
	        'info': "Will be your account",
	    },
	    'pwd': {
	        'info': "6 to 30 characters",
	        'error': "Shall be 6 to 30 characters"
	    },
	    'verify': {
	        'info': "Enter the password again",
	        'error': "Passwords do not match"
	    }
	}
};

ab.LIST_NAMES = [
	"Interested",
	"Reading",
	"Done"
];

/**
 * The max length of comment according to douban.
 * @type {Number}
 */
ab.COMMENT_LIMIT = 350;
