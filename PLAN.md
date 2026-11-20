# Implementation plan

The implementation follows `SPEC.md` and keeps the core dependency-free.

1. Keep the base62 encoder/decoder small and test its alphabet, zero, invalid
   inputs, and round trips.
2. Before implementing the hash table or shortener, write tests for the specified
   boundaries. Test the hash table through its public API and test the shortener
   against duplicate, invalid, and unknown inputs.
3. Implement `HashTable` using a list of linked-list bucket heads and explicit
   polynomial hashing. Do not use `dict`, `set`, or built-in `hash()`. Rehash all
   entries when the load factor exceeds 0.75.
4. Implement `URLShortener` on top of that table. Maintain a monotonically
   increasing integer ID for each new URL and base62-encode the ID; never derive
   a public code from the URL's hash.
5. Add a linear-probing table behind the same mapping interface, then rerun the
   same hash-table and shortener tests against both implementations.
6. Measure probe counts at fixed load factors with reproducible key sets, compare
   successful and unsuccessful search counts with theory, and save the table and
   SVG chart under `experiments/`.
7. Build the standard-library web server last, reusing the shortener and exposing
   its bucket/probe diagnostics at `/table`.
8. Run the full test suite and inspect generated experiment artifacts and the
   concise report before considering the work complete.

Tests remain unchanged once implementation starts; implementation must adapt to
the behavior already specified and tested.
