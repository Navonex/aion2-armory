<!-- Datenschutzerklärung (Vorlage). Beschreibt, was die Armory tatsächlich verarbeitet (Stand des Codes):
     Ändert sich, was gespeichert, protokolliert oder von fremden Servern geladen wird, hier nachziehen.
     Verantwortlicher und Hoster kommen aus der .env (ARMORY_OPERATOR_*, ARMORY_HOSTER). -->
<script lang="ts">
	import OperatorAddress from '#lib/components/OperatorAddress.svelte';
	import { i18n, t } from '#lib/i18n.svelte.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const hoster = $derived(data.info.hoster);
</script>

<svelte:head><title>{t('legal.privacy')} · AION 2 Armory</title></svelte:head>

<article class="glass pad legal-page">
	{#if i18n.lang === 'de'}
		<h1>Datenschutzerklärung</h1>
		<h2>1. Verantwortlich</h2>
		<OperatorAddress operator={data.info.operator} />
		<p>
			Die AION 2 Armory ist ein privates, nicht kommerzielles Angebot für eine Gilde (AION 2). Es gibt
			keine Werbung, kein Tracking und keine Analysewerkzeuge.
		</p>

		<h2>2. Hosting und Aufruf der Seite</h2>
		<p>
			Die Armory läuft auf einem Server{hoster ? ` (${hoster})` : ''}. Bei jedem Aufruf verarbeitet der
			Server technisch notwendig deine IP-Adresse, Zeitpunkt, aufgerufene Adresse, Anfragemethode und
			Statuscode und schreibt sie ins Protokoll. Das dient dem Betrieb, der Fehlersuche und der Abwehr von
			Angriffen (Art. 6 Abs. 1 lit. f DSGVO).
		</p>

		<h2>3. Kein Konto, keine Cookies</h2>
		<p>
			Die Armory hat keine Anmeldung und speichert keine Daten über dich als Besucher. Ist ein Passwort
			eingerichtet, merkt es sich dein Browser für die Sitzung. Im lokalen Speicher des Browsers liegt nur
			deine Sprachwahl (<code>armory.lang</code>). Cookies setzt die Armory nicht.
		</p>

		<h2>4. Charaktere in der Armory</h2>
		<p>
			Mitglieder der Gilde tragen Charaktere ein. Dazu speichert die Armory eine Momentaufnahme der
			öffentlichen Charakterseite von der offiziellen AION-2-Website (NCSOFT): Kampfkraft, Ausrüstung samt
			Werten, Titel, Skills, Daevanion. Sie wird einmal täglich und auf Knopfdruck neu geholt; je Tag bleiben
			Kampfkraft und Gegenstandsstufe als Verlauf. Das wird gelöscht, wenn der Charakter ausgetragen wird.
			Ein Vergleich lässt sich per Link teilen: gespeichert werden der Armory-Charakter sowie Name und Server
			des anderen Charakters, den die Armory beim Öffnen neu von der AION-2-Website holt, ohne ihn zu
			speichern. Der Build-Check holt auf Knopfdruck die Rangliste von Abyss Logs (abysslogs.com) und die
			öffentlichen Charakterseiten der besten Spieler; gespeichert wird nur die Auswertung, nicht deren Namen
			oder Daten. Geteilte Links gelten, bis sie zurückgezogen werden; Suchmaschinen werden gebeten, sie
			nicht aufzunehmen. Zweck ist die gemeinsame Auswertung in der Gilde (Art. 6 Abs. 1 lit. f DSGVO).
		</p>

		<h2>5. Inhalte von fremden Servern</h2>
		<p>
			Symbole von Fähigkeiten, Buffs und Gegenständen sowie Charakterbilder lädt dein Browser direkt von
			Servern des Spieleherstellers NCSOFT (<code>assets.playnccdn.com</code>,
			<code>profileimg.plaync.com</code>). Dabei erfährt NCSOFT deine IP-Adresse.
		</p>

		<h2>6. Deine Rechte</h2>
		<p>
			Du kannst Auskunft über deine Daten verlangen, ihre Berichtigung oder Löschung, die Einschränkung der
			Verarbeitung und die Herausgabe deiner Daten, und du kannst der Verarbeitung widersprechen (Art.
			15–21 DSGVO). Wende dich dafür an den Betreiber (oben). Außerdem kannst du dich bei einer
			Datenschutz-Aufsichtsbehörde beschweren.
		</p>
	{:else}
		<h1>Privacy policy</h1>
		<h2>1. Controller</h2>
		<OperatorAddress operator={data.info.operator} />
		<p>
			AION 2 Armory is a private, non-commercial site for a guild (AION 2). There are no ads, no tracking
			and no analytics.
		</p>

		<h2>2. Hosting and visiting the site</h2>
		<p>
			The Armory runs on a server{hoster ? ` (${hoster})` : ''}. For every request the server processes your
			IP address, time, requested address, method and status code and writes them to its log, for operation,
			debugging and defending against attacks (Art. 6(1)(f) GDPR).
		</p>

		<h2>3. No account, no cookies</h2>
		<p>
			The Armory has no login and stores nothing about you as a visitor. If a password is set, your browser
			remembers it for the session. The browser's local storage only holds your language
			(<code>armory.lang</code>). The Armory sets no cookies.
		</p>

		<h2>4. Characters in the Armory</h2>
		<p>
			Guild members add characters. The Armory stores a snapshot of the public character page from the
			official AION 2 website (NCSOFT): combat power, equipment with stats, titles, skills, Daevanion. It is
			refreshed once a day and on demand; combat power and item level per day are kept as history. All of it
			is deleted when the character is removed. A comparison can be shared by link: stored are the Armory
			character plus name and server of the other character, which is fetched live when the link is opened
			and not stored. The build check fetches the Abyss Logs leaderboard (abysslogs.com) and the public pages
			of the top players on demand; only the evaluation is stored, not their names or data. Shared links stay
			valid until withdrawn; search engines are asked not to index them. The purpose is shared analysis
			within the guild (Art. 6(1)(f) GDPR).
		</p>

		<h2>5. Content from other servers</h2>
		<p>
			Your browser loads icons and character images directly from servers of the game publisher NCSOFT
			(<code>assets.playnccdn.com</code>, <code>profileimg.plaync.com</code>), which see your IP address.
		</p>

		<h2>6. Your rights</h2>
		<p>
			You may request access to, correction or deletion of your data, restriction of processing and data
			portability, and you may object to processing (Art. 15–21 GDPR). Contact the operator (above). You can
			also complain to a data protection authority.
		</p>
	{/if}
</article>

<style>
	.legal-page {
		max-width: 760px;
		margin: 0 auto;
	}
	h1 {
		font-size: 28px;
	}
	h2 {
		font-size: 17px;
		margin: 26px 0 8px;
	}
	p,
	p {
		margin: 0 0 10px;
	}
	code {
		font-size: 13px;
	}
</style>
