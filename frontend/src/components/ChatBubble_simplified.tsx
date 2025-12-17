// Section simplifiée pour l'input avec émojis dans la bulle
// À remplacer dans ChatBubble.tsx aux lignes 449-816

{/* Input Area - Simplified with emojis inside */}
<div className="relative">
  <div className="relative bg-white border-2 border-gray-300 rounded-2xl shadow-sm focus-within:border-teal-500 focus-within:shadow-lg transition-all">
    {/* Left Icons - Simple emoji buttons */}
    <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
      {/* Country Selector - Always visible */}
      <div className="relative" ref={countryDropdownRef}>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setShowCountryDropdown(!showCountryDropdown);
          }}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title={selectedCountry ? selectedCountry.name : "Choisir un pays"}
        >
          {selectedCountry ? (
            selectedCountry.name.toLowerCase() === 'world' ? (
              <span className="text-xl">🌍</span>
            ) : (
              <img
                src={selectedCountry.flag}
                alt={selectedCountry.name}
                className="w-6 h-4 object-contain"
              />
            )
          ) : (
            <span className="text-xl">🌍</span>
          )}
        </button>

        {/* Country Dropdown */}
        {showCountryDropdown && (
          <div className="absolute left-0 top-full mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-[150] overflow-hidden" style={{ maxHeight: "260px" }}>
            <div className="p-2 border-b">
              <input
                type="text"
                value={countrySearch}
                onChange={(e) => setCountrySearch(e.target.value)}
                placeholder="Rechercher un pays..."
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                onMouseDown={(e) => e.stopPropagation()}
              />
            </div>
            <div
              className="overflow-y-auto scrollbar-thin"
              style={{ maxHeight: "200px" }}
              onMouseDown={(e) => e.stopPropagation()}
            >
              {filteredCountries.map((country, index) => (
                <button
                  key={`${country.code}-${index}`}
                  onClick={() => {
                    setSelectedCountry(country);
                    setSelectedLeague(null);
                    setSelectedMatch(null);
                    setShowCountryDropdown(false);
                    setCountrySearch("");
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-teal-50 flex items-center gap-3 transition-colors"
                >
                  {country.name.toLowerCase() === 'world' ? (
                    <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clipRule="evenodd" />
                    </svg>
                  ) : country.flag ? (
                    <img
                      src={country.flag}
                      alt={country.name}
                      className="w-6 h-4 object-contain"
                    />
                  ) : (
                    <div className="w-6 h-4 bg-gray-200 rounded" />
                  )}
                  <span className="text-sm">{country.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* League Selector - Only if country selected */}
      {selectedCountry && (
        <div className="relative" ref={leagueDropdownRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowLeagueDropdown(!showLeagueDropdown);
            }}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={selectedLeague ? selectedLeague.league.name : "Choisir une ligue"}
          >
            {selectedLeague ? (
              <img
                src={selectedLeague.league.logo || ''}
                alt={selectedLeague.league.name}
                className="w-5 h-5 object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            ) : (
              <span className="text-xl">🏆</span>
            )}
          </button>

          {/* League Dropdown - Same as before */}
          {showLeagueDropdown && (
            <div className="absolute left-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-[200] overflow-hidden" style={{ maxHeight: "260px" }}>
              <div className="p-2 border-b">
                <input
                  type="text"
                  value={leagueSearch}
                  onChange={(e) => setLeagueSearch(e.target.value)}
                  placeholder="Rechercher une ligue..."
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  onMouseDown={(e) => e.stopPropagation()}
                />
              </div>
              <div
                className="overflow-y-auto scrollbar-thin"
                style={{ maxHeight: "200px" }}
                onMouseDown={(e) => e.stopPropagation()}
              >
                {filteredLeagues.map((league) => (
                  <button
                    key={league.league.id}
                    onClick={() => {
                      setSelectedLeague(league);
                      setSelectedMatch(null);
                      setShowLeagueDropdown(false);
                      setLeagueSearch("");
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-teal-50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <img
                        src={league.league.logo || ''}
                        alt={league.league.name}
                        className="w-6 h-6 object-contain"
                        onError={(e) => {
                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="24" height="24"%3E%3Crect width="24" height="24" fill="%23e5e7eb" rx="4"/%3E%3C/svg%3E';
                        }}
                      />
                      <div className="flex flex-col">
                        <div className="font-medium text-sm flex items-center gap-2">
                          {league.country.flag && (
                            <img
                              src={league.country.flag}
                              alt={league.country.name}
                              className="w-4 h-3 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          )}
                          <span>{league.league.name}</span>
                        </div>
                        <div className="text-xs text-gray-500">{league.country.name}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Match Selector - Only if league selected */}
      {selectedLeague && (
        <div className="relative" ref={matchDropdownRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowMatchDropdown(!showMatchDropdown);
            }}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-1"
            title={selectedMatch ? `${selectedMatch.teams.home.name} vs ${selectedMatch.teams.away.name}` : "Choisir un match"}
          >
            {selectedMatch ? (
              <>
                <img
                  src={selectedMatch.teams.home.logo || ''}
                  alt={selectedMatch.teams.home.name}
                  className="w-5 h-5 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
                <span className="text-xs font-semibold text-gray-500">vs</span>
                <img
                  src={selectedMatch.teams.away.logo || ''}
                  alt={selectedMatch.teams.away.name}
                  className="w-5 h-5 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </>
            ) : (
              <span className="text-xl">⚽</span>
            )}
          </button>

          {/* Match Dropdown - Same as before with all filters */}
          {showMatchDropdown && (
            <div className="absolute left-0 top-full mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-[250] overflow-hidden" style={{ maxHeight: "310px" }}>
              {/* ... rest of match dropdown code ... */}
            </div>
          )}
        </div>
      )}
    </div>

    {/* Text Input */}
    <textarea
      value={inputValue}
      onChange={(e) => setInputValue(e.target.value)}
      onKeyPress={handleKeyPress}
      placeholder="Posez votre question..."
      rows={1}
      className="w-full py-4 bg-transparent focus:outline-none resize-none text-gray-900 placeholder-gray-400 text-sm sm:text-base"
      style={{
        minHeight: "56px",
        maxHeight: "200px",
        paddingLeft: selectedMatch ? "150px" : selectedLeague ? "100px" : selectedCountry ? "70px" : "16px",
        paddingRight: "100px"
      }}
    />

    {/* Right Icons - Actions */}
    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
      <button
        type="button"
        className="p-2 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
        title="Commande vocale"
      >
        <MicrophoneIcon className="w-5 h-5" />
      </button>

      <button
        onClick={handleSend}
        disabled={!inputValue.trim() || isLoading}
        className="p-2.5 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
        title="Envoyer"
      >
        <PaperAirplaneIcon className="w-5 h-5" />
      </button>
    </div>
  </div>
</div>
