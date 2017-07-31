(function() {(window.nunjucksPrecompiled = window.nunjucksPrecompiled || {})["query-resultset.html"] = (function() {
function root(env, context, frame, runtime, cb) {
var lineno = null;
var colno = null;
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
output += " rows)\n        </div>\n        <div class='col-md-4'>\n            <div class=\"btn-group pull-right\">\n                <button type=\"button\" class=\"btn btn-info btn-xs dropdown-toggle\" data-toggle=\"dropdown\">\n                    Download data <span class=\"caret\"></span>\n                </button>\n                <ul class=\"dropdown-menu\" role=\"menu\">\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/tsv?download=true\">TSV</a></li>\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/json?download=true\">JSON</a></li>\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/json-lines?download=true\">JSON Lines</a></li>\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/csv?download=true\">CSV</a></li>\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/wikitable?download=true\">Wikitable</a></li>\n                    <li><a href=\"/run/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "run_id"), env.opts.autoescape);
output += "/output/";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_id"), env.opts.autoescape);
output += "/xlsx?download=true\">Excel XLSX</a></li>\n                </ul>\n            </div>\n        </div>\n    </div>\n    <table class='table'></table>\n</div>\n";
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
var lineno = null;
var colno = null;
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
output += "\nThis query is currently executing... \n";
if(runtime.memberLookup((runtime.contextOrFrameLookup(context, frame, "extra")),"connection_id")) {
output += "\n<button id=\"show-explain\" type=\"button\" class=\"btn btn-default btn-xs\">Explain</button>\n";
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

