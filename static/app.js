function sendValue(v){
fetch('/message?value='+encodeURIComponent(v))
.then(r=>r.json())
.then(console.log);
}