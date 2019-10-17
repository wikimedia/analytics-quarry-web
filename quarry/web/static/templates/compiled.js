(function() {(window.nunjucksPrecompiled = window.nunjucksPrecompiled || {})["query-resultset.html"] = (function() {
function root(env, context, frame, runtime, cb) {
var lineno = 0;
var colno = 0;
var output = "";
try {
var parentTemplate = null;
output += "<div>\n    <div class=\"row resultset-header\">\n        <div class='resultset-header col-md-8'>\n            ";
if(runtime.contextOrFrameLookup(context, frame, "only_resultset")) {
output += "\n            Resultset\n            ";
;
}
else {
output += "\n            Resultset ";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_number"), env.opts.autoescape);
output += "\n            ";
;
}
output += "\n            (";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "rowcount"), env.opts.autoescape);
output += " rows)\n        </div>\n        <div class='col-md-4'>\n            <div class=\"btn-group pull-right\">\n                <button type=\"button\" class=\"btn btn-info btn-xs dropdown-toggle\" data-toggle=\"dropdown\">\n                    Download data <span class=\"caret\"></span>\n                </button>\n                <ul class=\"dropdown-menu\" role=\"menu\">\n                    ";
frame = frame.push();
var t_3 = {"tsv": "TSV","json": "JSON","json-lines": "JSON Lines","csv": "CSV","wikitable": "Wikitable","html": "HTML","xlsx": "Excel XLSX"};
if(t_3) {t_3 = runtime.fromIterator(t_3);
var t_1;
if(runtime.isArray(t_3)) {
var t_2 = t_3.length;
for(t_1=0; t_1 < t_3.length; t_1++) {
var t_4 = t_3[t_1][0];
frame.set("[object Object]", t_3[t_1][0]);
var t_5 = t_3[t_1][1];
frame.set("[object Object]", t_3[t_1][1]);
frame.set("loop.index", t_1 + 1);
frame.set("loop.index0", t_1);
frame.set("loop.revindex", t_2 - t_1);
frame.set("loop.revindex0", t_2 - t_1 - 1);
frame.set("loop.first", t_1 === 0);
frame.set("loop.last", t_1 === t_2 - 1);
frame.set("loop.length", t_2);
output += "\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/";
output += runtime.suppressValue(t_4, env.opts.autoescape);
output += "\" download=\"quarry-";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "query_id"), env.opts.autoescape);
output += "-";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "slugify_title"), env.opts.autoescape);
output += "-run";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += ".";
output += runtime.suppressValue(t_4, env.opts.autoescape);
output += "\">";
output += runtime.suppressValue(t_5, env.opts.autoescape);
output += "</a></li>\n                    ";
;
}
} else {
t_1 = -1;
var t_2 = runtime.keys(t_3).length;
for(var t_6 in t_3) {
t_1++;
var t_7 = t_3[t_6];
frame.set("format", t_6);
frame.set("formatname", t_7);
frame.set("loop.index", t_1 + 1);
frame.set("loop.index0", t_1);
frame.set("loop.revindex", t_2 - t_1);
frame.set("loop.revindex0", t_2 - t_1 - 1);
frame.set("loop.first", t_1 === 0);
frame.set("loop.last", t_1 === t_2 - 1);
frame.set("loop.length", t_2);
output += "\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/";
output += runtime.suppressValue(t_6, env.opts.autoescape);
output += "\" download=\"quarry-";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "query_id"), env.opts.autoescape);
output += "-";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "slugify_title"), env.opts.autoescape);
output += "-run";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += ".";
output += runtime.suppressValue(t_6, env.opts.autoescape);
output += "\">";
output += runtime.suppressValue(t_7, env.opts.autoescape);
output += "</a></li>\n                    ";
;
}
}
}
frame = frame.pop();
output += "\n                </ul>\n            </div>\n        </div>\n    </div>\n    <table class='table'></table>\n</div>\n";
if(parentTemplate) {
parentTemplate.rootRenderFunc(env, context, frame, runtime, cb);
} else {
cb(null, output);
}
;
} catch (e) {
  cb(runtime.handleError(e, lineno, colno));
}
}
return {
root: root
};

})();
})();
(function() {(window.nunjucksPrecompiled = window.nunjucksPrecompiled || {})["query-status.html"] = (function() {
function root(env, context, frame, runtime, cb) {
var lineno = 0;
var colno = 0;
var output = "";
try {
var parentTemplate = null;
if(runtime.contextOrFrameLookup(context, frame, "status") == "failed") {
output += "\n<strong>Error</strong>\n<pre>";
output += runtime.suppressValue(runtime.memberLookup((runtime.contextOrFrameLookup(context, frame, "extra")),"error"), env.opts.autoescape);
output += "</pre>\n";
;
}
else {
if(runtime.contextOrFrameLookup(context, frame, "status") == "killed") {
output += "\nThis query took longer than 30 minutes to execute and was killed.\n";
;
}
else {
if(runtime.contextOrFrameLookup(context, frame, "status") == "queued") {
output += "\nThis query is waiting to be executed\n";
;
}
else {
if(runtime.contextOrFrameLookup(context, frame, "status") == "running") {
output += "\nThis query is currently executing...\n";
if(runtime.memberLookup((runtime.contextOrFrameLookup(context, frame, "extra")),"connection_id")) {
output += "\n<!--<button id=\"show-explain\" type=\"button\" class=\"btn btn-default btn-xs\">Explain</button>-->\n";
;
}
output += "\n";
;
}
;
}
;
}
;
}
output += "\n";
if(parentTemplate) {
parentTemplate.rootRenderFunc(env, context, frame, runtime, cb);
} else {
cb(null, output);
}
;
} catch (e) {
  cb(runtime.handleError(e, lineno, colno));
}
}
return {
root: root
};

})();
})();

