/*
 * @author: Andriy Lin
 * for booklists' pages
 */

// Andriy Books namespace
var ab = ab || {};

/**
 * Validate the actions select box.
 * Stop submitting when no option is selected.
 */
ab.initBooklistActions = function() {
	var form = document.getElementById('action_form');
	var select = document.getElementById('action_select');

	form.onsubmit = function() {
		if (!select.value) {
			return false;
		}
		if (select.value == 'import') {
			return confirm('All local records in this list will be deleted and re-imported.\nAre you sure to continue?');
		}
		return true;
	};
};
