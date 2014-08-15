(function() {(window.nunjucksPrecompiled = window.nunjucksPrecompiled || {})["query-resultset.html"] = (function() {function root(env, context, frame, runtime, cb) {
var lineno = null;
var colno = null;
var output = "";
try {
output += "<div>\n    <span class='resultset-header'>\n        ";
if(runtime.contextOrFrameLookup(context, frame, "only_resultset")) {
output += "\n        Resultset\n        ";
;
}
else {
output += "\n        Resultset ";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "resultset_number"), env.autoesc);
output += "\n        ";
;
}
output += "\n        (";
output += runtime.suppressValue(runtime.contextOrFrameLookup(context, frame, "rowcount"), env.autoesc);
output += " rows)\n    </span>\n    <table class='table'></table>\n</div>\n";
cb(null, output);
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
(function() {(window.nunjucksPrecompiled = window.nunjucksPrecompiled || {})["query-status.html"] = (function() {function root(env, context, frame, runtime, cb) {
var lineno = null;
var colno = null;
var output = "";
try {
if(runtime.contextOrFrameLookup(context, frame, "status") == "failed") {
output += "\n<strong>Error</strong>\n<pre>";
output += runtime.suppressValue(runtime.memberLookup((runtime.contextOrFrameLookup(context, frame, "extra")),"error", env.autoesc), env.autoesc);
output += "</pre>\n";
;
}
else {
if(runtime.contextOrFrameLookup(context, frame, "status") == "killed") {
output += "\nYour query took longer than 10 minutes to execute and was killed.\n";
;
}
else {
if(runtime.contextOrFrameLookup(context, frame, "status") == "queued") {
output += "\nYour query is waiting to be executed\n";
;
}
else {
if(runtime.contextOrFrameLookup(context, frame, "status") == "running") {
output += "\nYour query is currently executing\n";
;
}
;
}
;
}
;
}
output += "\n";
cb(null, output);
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

