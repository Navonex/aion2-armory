// Angemeldete Module. Ein neues Modul bekommt hier eine Zeile; Menü und Texte ergeben sich daraus.
import type { Me } from '#lib/api.ts';
import { addTexts } from '#lib/i18n.svelte.ts';
import type { HubModule, NavItem } from '#lib/module.ts';
import { CORE_TEXTS } from '#lib/texts.ts';
import armory from '#modules/armory/module.ts';
import bis from '#modules/bis/module.ts';
import { TEXTS as PROFILE_TEXTS } from '#modules/logs/texts.ts';

export const MODULES: HubModule[] = [armory, bis];

addTexts(CORE_TEXTS);
addTexts(PROFILE_TEXTS); // Texte der Profil-Ansicht (modules/logs/components)
for (const m of MODULES) if (m.texts) addTexts(m.texts);

/** Seitenleiste: Übersicht, dann die Module, am Ende die Admin-Seiten des Kerns. */
export const NAV: NavItem[] = [
	{ href: '/hub', label: 'nav.overview', icon: 'home' },
	...MODULES.flatMap((m) => m.nav)
];

/** Was dieses Konto im Menü sieht: Admin-Seiten nur für Admins. */
export const navFor = (me: Me): NavItem[] => NAV.filter((i) => !i.admin || me.role === 'admin');

/** Ein Eintrag der Seitenleiste: eine Seite, oder ein Spiel mit seinen Seiten (`pages`). */
export type MenuEntry = NavItem & { pages: NavItem[] };

/** Fasst die Einträge eines Spiels zu einem zusammen. Er führt zur ersten Seite des Spiels und
 *  trägt deren Symbol; die Seiten selbst zeigt das Layout als Reiter über dem Inhalt. */
export function menu(items: NavItem[]): MenuEntry[] {
	const entries: MenuEntry[] = [];
	for (const item of items) {
		const game = item.game ? entries.find((e) => e.label === item.game) : undefined;
		if (game) game.pages.push(item);
		else if (item.game) entries.push({ ...item, label: item.game, pages: [item] });
		else entries.push({ ...item, pages: [] });
	}
	return entries;
}
