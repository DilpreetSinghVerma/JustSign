this.imgcontain = function (node) {
	var name = node.nodeName.toLowerCase();

	// Only work on IMG nodes
	if (name != "img") return;
	
	// restrict to valid object-fit value
	var objectFit = node.currentStyle['object-fit'];

	if (!objectFit || !/^(contain)$/.test(objectFit)) return;

	// prepare container styles
	// var outerWidth  = node.clientWidth;
	// var outerHeight = node.clientHeight;
	var outerWidth = node.parentNode.clientWidth;
	var outerHeight = node.parentNode.clientHeight;
	// Check for change
	if (!node.prevWidth || !node.prevHeight || node.prevWidth != outerWidth || node.prevHeight != outerHeight) {

		var outerRatio  = outerWidth / outerHeight;
		// console.log("#imgcontain ouWi="+outerWidth+" ouHi="+outerHeight+" ouRt="+outerRatio);

		var naturalWidth = node.naturalWidth;
		// May not yet have natural dimensions
		if (naturalWidth) {
			var naturalHeight = node.naturalHeight;
			var naturalRatio = naturalWidth / naturalHeight;
			// console.log("#imgcontain naWi="+naturalWidth+" naHi="+naturalHeight+" naRt="+naturalRatio);

			var rtCSS = node.runtimeStyle;
			if (outerRatio > naturalRatio) {
				// Wider than needed so space at sides
				var padSide = Math.round((outerWidth - outerHeight * naturalRatio) / 2);
				// console.log("#imgcontain ouWi="+outerWidth+" siPa="+padSide+" imWi="+ (outerWidth - 2 * padSide));
				// TB RL
				rtCSS.padding = "0px "+padSide+"px";
			} else {
				// Higher than needed so space at top and bottom
				var padTop = Math.round((outerHeight - outerWidth / naturalRatio) / 2);
				// console.log("#imgcontain ouHi="+outerHeight+" toPa="+padTop+" inHi=" + (outerHeight - 2 * padTop));
				rtCSS.padding = padTop+"px 0px";
			}
			// Record change
			node.prevWidth = outerWidth;
			node.prevHeight = outerHeight;
		}
	} else {
	 	// console.log("#imgcontain clWi="+outerWidth+" clHi="+outerHeight+" [same]");
	}
};

this.imagefit = function () {
	// console.log("#imagefit called");
	if (document.body) {
		var all = document.getElementsByClassName("imagefit");
		if (all.length > 0) {
			var index = -1;
			while (all[++index]) imgcontain(all[index]);
			// and repeat unfortunately
			setTimeout(imagefit, 100);
		} else {
			console.log("#imagefit ending");
		}
	} else {
		console.log("#imagefit body still loading");
		setTimeout(imagefit);
	}
};

if (/MSIE|Trident/.test(navigator.userAgent)) this.imagefit();

