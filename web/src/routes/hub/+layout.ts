import type { LayoutLoad } from './$types';

// Ohne Login: /api/me liefert immer das Konto „Gilde“ (api/armory_api/deps.py)
export const load: LayoutLoad = async ({ parent }) => {
	const { me } = await parent();
	return { me: me! };
};
