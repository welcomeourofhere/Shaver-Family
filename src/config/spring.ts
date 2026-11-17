import design from './design.json' with { type: 'json' };

// CSS transitions and scripted motion sample the same damped oscillator.
export const spring = design.spring;
const materialDamping=Math.max(spring.windowDamping,2*Math.sqrt(spring.stiffness*spring.mass));
export function springProgress(progress: number, damping=spring.damping): number {
  if (progress <= 0) return 0;
  if (progress >= 1) return 1;
  const frequency = Math.sqrt(spring.stiffness / spring.mass);
  const decay = damping / (2 * spring.mass);
  const response = (time: number) => {
    if(Math.abs(decay-frequency)<.0001)return 1-(1+frequency*time)*Math.exp(-frequency*time);
    if(decay>frequency){
      const root=Math.sqrt(decay*decay-frequency*frequency),a=-decay+root,b=-decay-root;
      return 1-(b*Math.exp(a*time)-a*Math.exp(b*time))/(b-a);
    }
    const damped=Math.sqrt(frequency*frequency-decay*decay);
    return 1-Math.exp(-decay*time)*(Math.cos(damped*time)+decay/damped*Math.sin(damped*time));
  };
  return response(progress * spring.settleMs / 1000) / response(spring.settleMs / 1000);
}
// Bounded material cannot overshoot a size floor or an alpha endpoint.
// Critical damping lets all properties use the full shared duration before settling.
export function boundedSpringProgress(progress:number):number {
  return springProgress(progress,materialDamping);
}
const sampleSpring=(damping:number)=>`linear(${Array.from({length:spring.samples+1},(_,i)=>springProgress(i/spring.samples,damping).toFixed(6)).join(",")})`;
// Material strain follows the velocity of the same spring, not a second wobble.
export function springShape(progress:number, strength:number, damping=spring.damping, widthWeight=1/design.scale.goldenRatio) {
  if(progress<=0||progress>=1)return {x:1,y:1};
  const step=1/spring.samples,start=Math.max(0,progress-step),end=Math.min(1,progress+step);
  const frequency=Math.sqrt(spring.stiffness/spring.mass)*spring.settleMs/1000;
  const strain=strength*(springProgress(end,damping)-springProgress(start,damping))/(end-start)/frequency;
  return {x:1-strain*widthWeight,y:1+strain};
}
// A bounded displacement supplies the material tension while the same spring's
// velocity supplies its release. The painted layer deforms; its hit target does not.
export function boundedMaterialShape(progress:number,strength:number) {
  const p=boundedSpringProgress(progress),velocity=springShape(progress,strength,materialDamping);
  const tension=strength*p*(1-p);
  return{x:velocity.x-tension/design.scale.goldenRatio,y:velocity.y+tension};
}
export const windowSpringCSS=sampleSpring(spring.windowDamping);
export const popoverSpringCSS=sampleSpring(spring.popoverDamping);
export const springCSS = `linear(${Array.from({length: spring.samples + 1}, (_, i) => springProgress(i / spring.samples).toFixed(6)).join(',')})`;
export const drawerSpringCSS = `linear(${Array.from({length: spring.samples + 1}, (_, i) => springProgress(i / spring.samples,spring.drawerDamping).toFixed(6)).join(',')})`;

export function stepSpring(value: number, velocity: number, target: number, elapsed: number, damping=spring.damping) {
  const steps = Math.max(1, Math.ceil(Math.min(elapsed, .04) * 120));
  const dt = Math.min(elapsed, .04) / steps;
  for (let i = 0; i < steps; i++) {
    velocity += ((target - value) * spring.stiffness - velocity * damping) / spring.mass * dt;
    value += velocity * dt;
  }
  return Math.abs(value-target)<spring.epsilon && Math.abs(velocity)<spring.epsilon
    ? {value:target,velocity:0} : {value,velocity};
}
