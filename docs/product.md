# Gadiruta Product Definition

## Goal

Gadiruta is a Cádiz-area public transport web app inspired conceptually by Rome2Rio, but intentionally narrower for the first version.

The MVP should make local public transport easier to use for:

- finding direct public transport between two places;
- checking scheduled departures for a chosen date and time;
- browsing lines and stops;
- seeing relevant service notices.

The first version does **not** calculate journeys requiring transfers.

## Product principles

Gadiruta should feel simple, fast, mobile-first, friendly, spacious, and immediately understandable. Use [clicks.coffee](https://clicks.coffee/) as an aesthetic reference without copying it literally: strong typography, generous whitespace, restrained color, large controls, rounded surfaces, little visual clutter, and one obvious primary task per screen.

Avoid the look and information density of a traditional transit-authority website.

## Language

Project code, documentation, commits, and API field names are written in English.

The UI supports English and Spanish from the beginning. English is the source/fallback language. All user-facing strings go through the translation system; official place and operator names are preserved as provided by the data source.

## MVP experience

### Home and journey search

The primary interaction is an origin/destination search with:

- population-centre autocomplete;
- easy origin/destination swap;
- date selection;
- optional departure-time filtering;
- a clear Find transport action.

Search state should be represented in the URL so searches can be shared and restored.

Population centres such as Cádiz, San Fernando, El Puerto de Santa María, and Jerez are the user-facing search unit. Users should not have to select an individual physical stop before searching.

### Direct journeys

A direct journey is a single scheduled trip that serves an origin stop before a destination stop and operates on the requested date.

For each result, show as much as the source data reliably supports, especially:

- departure and arrival time;
- duration;
- line and transport mode;
- operator;
- origin and destination stop;
- relevant service notices.

Results must be easy to scan on a phone. If no direct service exists, make clear that routes requiring transfers are not supported yet rather than implying that no public-transport journey is possible.

### Lines and stops

The MVP should support browsing/searching lines and opening useful line details such as operator, directions, ordered stops, timetable, and relevant notices.

Stop/location detail should expose serving lines, upcoming scheduled services where available, direction/destination, and relevant notices.

Maps are not required for the MVP, but coordinates and route geometry should be retained when available.

### Alerts

Service notices should appear in context. A notice affecting a line should be visible from that line and from journey results that use it where the relationship can be established reliably.

### Favorites and recent searches

Authentication is not required for the MVP. Recent searches and favorites may be stored in `localStorage`, with a format that can later migrate to server-side accounts if accounts are introduced.

## Data product principles

The frontend consumes Gadiruta's own API and domain model, never raw upstream payloads.

GTFS is the planned authoritative source for static transit-network and schedule data. CTAN REST remains only for capabilities GTFS does not provide reliably, such as population-centre metadata, alerts, or supplementary provider-specific information.

Gadiruta should show data freshness where useful and must clearly state that it is an independent application using information from the Red de Consorcios de Transporte de Andalucía. Do not imply CTAN or Junta de Andalucía endorsement.

## Scope boundaries

The MVP does not include:

- transfer routing;
- arbitrary street-address routing;
- walking or driving directions;
- flights;
- payments;
- authentication/accounts;
- push notifications;
- complex map functionality;
- full Andalusia coverage;
- a custom general-purpose routing algorithm.

## Roadmap

### Current product state

The backend/frontend foundation, bilingual population-centre search, date/time controls, and an initial direct-journey flow are implemented. The current direct-journey implementation uses CTAN REST and carries date/calendar limitations that are being retired rather than expanded.

### Immediate next milestone: GTFS migration

Move static transit data and direct-journey lookup to CTAN's GTFS feed:

- import stops, routes, trips, stop times, calendars, calendar exceptions, agencies, and shapes;
- associate user-facing places with GTFS stops;
- answer direct-journey searches from local imported data;
- validate coverage and identify any additional feeds needed for rail, tram, ferry, or other modes;
- keep only justified CTAN REST dependencies.

This migration is part of the MVP foundation, not future transfer routing.

### Post-MVP

After the core first-version journey, line, stop, alert, localization, and responsive experience is polished, prioritize an installable PWA built from the existing React + Vite frontend. Later additions may include maps, nearby stops, fares, and richer favorites.

### Later routing

For journeys requiring transfers, use GTFS with a mature transit-routing engine such as OpenTripPlanner rather than building a routing engine in Gadiruta. Additional providers/feeds can be added when Cádiz coverage requires them.
