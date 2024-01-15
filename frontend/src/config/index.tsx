// export const BASE_URL: string = 'http://localhost:8000';
// export const BACKEND_URL: string =
//   'http://localhost:8000/api/v1';

// Testing without Docker on VM:
// export const BASE_URL: string = 'http://192.168.1.30:8000';
// export const BACKEND_URL: string = 'http://192.168.1.30:8000/api/v1';
export const BASE_URL: string = process.env.NODE_ENV === 'production' ? "http://localhost:8000" : String(process.env.REACT_APP_BACKEND_URL)
export const BACKEND_URL: string = process.env.NODE_ENV === 'production' ? "http://localhost:8000/api/v1" : String(process.env.REACT_APP_BACKEND_URL) + "/api/v1"

console.log(process.env.NODE_ENV)
console.log(BASE_URL)
console.log(BACKEND_URL)