import { writable } from 'svelte/store';

// 1. التوكن واليوزر
const storedToken = localStorage.getItem('token');
const storedUser = localStorage.getItem('user');

export const token = writable(storedToken);
export const user = writable(storedUser ? JSON.parse(storedUser) : null);

// 2. التحكم بالصفحات - تأكدي إنها 'home' كنص
export const currentPage = writable('home');

// 3. المعرفات المطلوبة (تأكدي من وجود الـ export للكل)
export const selectedSessionId = writable(null);
export const selectedTeacherId = writable(null); 

// حفظ التغييرات تلقائياً
token.subscribe(val => val ? localStorage.setItem('token', val) : localStorage.removeItem('token'));
user.subscribe(val => val ? localStorage.setItem('user', JSON.stringify(val)) : localStorage.removeItem('user'));