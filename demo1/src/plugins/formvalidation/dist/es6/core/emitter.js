export default function s(){return{fns:{},clear(){this.fns={}},emit(s,...f){(this.fns[s]||[]).map((s=>s.apply(s,f)))},off(s,f){if(this.fns[s]){const n=this.fns[s].indexOf(f);if(n>=0){this.fns[s].splice(n,1)}}},on(s,f){(this.fns[s]=this.fns[s]||[]).push(f)}}}