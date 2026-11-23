export function poll(callback, delay) {
  let timer;
  let active = true;
  const step = async () => {
    try { await callback(); }
    finally { if (active) timer = setTimeout(step, delay); }
  };
  timer = setTimeout(step, delay);
  return () => { active = false; clearTimeout(timer); };
}
