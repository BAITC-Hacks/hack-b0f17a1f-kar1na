// Empty locally: FastAPI or the Vite proxy serves these paths on the same origin.
const backendOrigin = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');

export function backendUrl(path) {
  return `${backendOrigin}${path}`;
}
