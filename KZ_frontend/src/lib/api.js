import axios from 'axios';
import { get } from 'svelte/store';
import { token } from './stores';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000', // رابط البايكند
});

// يضيف التوكن لكل طلب اوتوماتيكياً
api.interceptors.request.use((config) => {
    const t = get(token);
    if (t) config.headers.Authorization = `Bearer ${t}`;
    return config;
});

export default api;