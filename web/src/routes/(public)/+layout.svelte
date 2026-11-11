<!-- Öffentlicher Bereich: geteilte Vergleiche und Build-Checks, Impressum, Datenschutz (immer ohne Passwort). -->
<script lang="ts">
	import Brand from '#lib/components/Brand.svelte';
	import LangSwitch from '#lib/components/LangSwitch.svelte';
	import LegalLinks from '#lib/components/LegalLinks.svelte';
	import { t } from '#lib/i18n.svelte.ts';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();
</script>

<header class="glass">
	<Brand />
	<div class="right">
		<LangSwitch />
		<a class="btn primary small" href="/hub/armory">{t('shell.toHub')}</a>
	</div>
</header>

<main>
	{@render children()}
</main>

<footer><LegalLinks /></footer>

<style>
	header {
		position: sticky;
		top: 12px;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		max-width: 1100px;
		margin: 12px auto 0;
		min-height: 56px;
		padding: 10px 12px 10px 18px;
		border-radius: var(--radius);
	}
	footer {
		display: flex;
		justify-content: center;
		padding: 0 16px 32px;
	}
	.right {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	main {
		max-width: 1100px;
		margin: 0 auto;
		padding: 48px 16px;
	}
	@media (max-width: 1132px) {
		header {
			margin: 12px 16px 0;
		}
	}
</style>
