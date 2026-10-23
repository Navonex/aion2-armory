import { redirect } from '@sveltejs/kit';

// Die Startseite führt direkt zur Armory
export const load = () => redirect(307, '/hub/armory');
