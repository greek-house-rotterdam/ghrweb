/**
 * Make /admin open the right language file of a draft (#126).
 *
 * A draft's branch holds the Greek file the editor saved, plus the Dutch and
 * English files the translation bot adds. When Decap reopens a draft, it
 * takes the branch's changed `.md` files, sorts them by path length and opens
 * the first one. The three paths are the same length, so GitHub's alphabetical
 * order wins and `en/…` opens instead of `gr/…`. Saving would then write the
 * editor's change into the English file.
 *
 * Fix: before Decap reads a draft, keep only the `.md` files inside the
 * draft's own collection folder (e.g. src/content/news/gr/ for "news-gr").
 * Other files (images) are left alone. Collections without a folder (site
 * settings) are left alone too.
 *
 * Loading order (index.html): `window.CMS_MANUAL_INIT = true`, then
 * decap-cms.js, then this file, which patches the GitHub backend and starts
 * Decap. It always starts Decap, even if the patch fails.
 *
 * This depends on Decap internals (`getBackend("github").init` and the
 * backend's `unpublishedEntry`), checked in Decap 3.16.3. Decap is pinned:
 * re-test this on every upgrade (open a translated draft and check that the
 * Greek text shows).
 */
(function (root) {
  "use strict";

  /**
   * Keep only the collection's own entry files in an unpublished entry's diff
   * list. Returns the data unchanged when it can't tell which files belong.
   */
  function ownFiles(data, collections) {
    if (!data || !Array.isArray(data.diffs) || !Array.isArray(collections)) return data;
    var collection = collections.find(function (c) {
      return c && c.name === data.collection;
    });
    if (!collection || !collection.folder) return data;
    var ext = "." + (collection.extension || "md");
    var folder = String(collection.folder).replace(/\/+$/, "") + "/";
    var diffs = data.diffs.filter(function (d) {
      var path = String(d && d.path);
      return !path.endsWith(ext) || path.indexOf(folder) === 0;
    });
    var hasEntryFile = diffs.some(function (d) {
      return String(d.path).endsWith(ext);
    });
    return hasEntryFile ? Object.assign({}, data, { diffs: diffs }) : data;
  }

  /** Wrap the GitHub backend so every draft goes through ownFiles(). */
  function patch(CMS) {
    var github = CMS && typeof CMS.getBackend === "function" && CMS.getBackend("github");
    if (!github || typeof github.init !== "function") return false;
    var init = github.init;
    github.init = function (config, options) {
      var impl = init(config, options);
      var original = impl && impl.unpublishedEntry;
      if (typeof original === "function") {
        impl.unpublishedEntry = function (args) {
          return Promise.resolve(original.call(impl, args)).then(function (data) {
            return ownFiles(data, config && config.collections);
          });
        };
      }
      return impl;
    };
    return true;
  }

  root.ghrOpenOwnLanguage = { ownFiles: ownFiles, patch: patch };

  var CMS = root.CMS;
  try {
    if (!patch(CMS)) console.error("open-own-language: Decap's GitHub backend not found; drafts may open the wrong language (#126).");
  } catch (error) {
    console.error("open-own-language: patch failed (#126)", error);
  } finally {
    if (CMS && typeof CMS.init === "function") CMS.init();
  }
})(typeof window !== "undefined" ? window : globalThis);
