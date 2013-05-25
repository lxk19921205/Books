/*
 * @author: Andriy Lin
 * for sign-up page
 */

// Andriy Books namespace
var ab = ab || {};

/**
 * If user chooses "remove" in the booklist selection form
 * other related tags, rating, comment will also be deleted!
 * Need to confirm that selection.
 */
ab.confirm_list_selection = function() {

	for (var idx in ab.LIST_NAMES) {
		var radioButton = document.getElementById("radio_" + ab.LIST_NAMES[idx]);
		if (radioButton.checked) {
			// one of the normal selection is checked, no need to worry
			return true;
		}
	}

	var removeButton = document.getElementById("radio_list_remove");
	if (removeButton.checked) {
		return confirm("Remove from any lists would also clear any related Rating, Comment, or Tags! \n\n Are you sure to remove?");
	}

	return true;
};


/**
 * Init the relationship between the rating "range" and its "output".
 */
ab.initRatingForm = function() {
	// the following lines are for rating selection
	var rating_form = document.getElementById('rating_form');
	var rating_range = document.getElementById('rating_range');
	var rating_output = document.getElementById('rating_output');

	rating_form.oninput = function() {
		if (rating_range.value == 0) {
			rating_output.value = "clear";
		} else if (rating_range.value == 1) {
			rating_output.value = rating_range.value + " star";
		} else {
			rating_output.value = rating_range.value + " stars";
		}
	};
	rating_form.oninput();
};

/**
 * There is a max amount limit for comment -- 350 characters.
 * If the comment exceeds the limit, stop submitting.
 */
ab.initCommentForm = function() {
	form = document.getElementById('comment_form');
	textarea = document.getElementById('comment_textarea');

	form.onsubmit = function() {
		if (textarea.value.length > ab.COMMENT_LIMIT) {
			alert('At most " + ab.COMMENT_LIMIT + " characters for comment, current: ' + textarea.value.length);
			return false;
		} else {
			return true;
		}
	};
};
