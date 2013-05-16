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
}
