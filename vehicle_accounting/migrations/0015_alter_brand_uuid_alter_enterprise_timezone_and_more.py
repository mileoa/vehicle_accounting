# Generated by Django 5.1.5 on 2025-04-13 11:34

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicle_accounting", "0014_generate_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="brand",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="enterprise",
            name="timezone",
            field=models.CharField(
                choices=[
                    ("America/Iqaluit", "America/Iqaluit"),
                    ("Africa/Dar_es_Salaam", "Africa/Dar_es_Salaam"),
                    ("Europe/Dublin", "Europe/Dublin"),
                    ("Chile/Continental", "Chile/Continental"),
                    ("UTC", "UTC"),
                    ("America/Yellowknife", "America/Yellowknife"),
                    ("Africa/Sao_Tome", "Africa/Sao_Tome"),
                    ("Asia/Tbilisi", "Asia/Tbilisi"),
                    ("Pacific/Pitcairn", "Pacific/Pitcairn"),
                    ("Europe/Guernsey", "Europe/Guernsey"),
                    ("Europe/Brussels", "Europe/Brussels"),
                    ("Antarctica/Casey", "Antarctica/Casey"),
                    ("Europe/Belfast", "Europe/Belfast"),
                    ("Europe/Tirane", "Europe/Tirane"),
                    ("America/Edmonton", "America/Edmonton"),
                    ("Etc/GMT+11", "Etc/GMT+11"),
                    ("Africa/Nouakchott", "Africa/Nouakchott"),
                    ("Asia/Dushanbe", "Asia/Dushanbe"),
                    ("Pacific/Samoa", "Pacific/Samoa"),
                    ("Asia/Jakarta", "Asia/Jakarta"),
                    ("America/Fortaleza", "America/Fortaleza"),
                    ("Etc/GMT-12", "Etc/GMT-12"),
                    ("Africa/Tripoli", "Africa/Tripoli"),
                    ("Africa/Dakar", "Africa/Dakar"),
                    ("America/Belize", "America/Belize"),
                    ("Europe/Malta", "Europe/Malta"),
                    ("Etc/GMT-0", "Etc/GMT-0"),
                    ("Pacific/Chatham", "Pacific/Chatham"),
                    ("Asia/Ulan_Bator", "Asia/Ulan_Bator"),
                    ("Antarctica/DumontDUrville", "Antarctica/DumontDUrville"),
                    ("America/Panama", "America/Panama"),
                    ("Antarctica/South_Pole", "Antarctica/South_Pole"),
                    ("Asia/Dubai", "Asia/Dubai"),
                    ("America/Lima", "America/Lima"),
                    ("Pacific/Fakaofo", "Pacific/Fakaofo"),
                    ("Asia/Tashkent", "Asia/Tashkent"),
                    ("Asia/Vladivostok", "Asia/Vladivostok"),
                    ("Europe/Simferopol", "Europe/Simferopol"),
                    ("Indian/Maldives", "Indian/Maldives"),
                    ("UCT", "UCT"),
                    ("America/Noronha", "America/Noronha"),
                    ("Europe/Oslo", "Europe/Oslo"),
                    ("Africa/Accra", "Africa/Accra"),
                    ("Atlantic/St_Helena", "Atlantic/St_Helena"),
                    ("Europe/Bratislava", "Europe/Bratislava"),
                    ("America/Thunder_Bay", "America/Thunder_Bay"),
                    ("Europe/Isle_of_Man", "Europe/Isle_of_Man"),
                    ("Etc/Zulu", "Etc/Zulu"),
                    ("Africa/Ouagadougou", "Africa/Ouagadougou"),
                    ("Africa/Khartoum", "Africa/Khartoum"),
                    ("US/Central", "US/Central"),
                    ("EST", "EST"),
                    (
                        "America/Argentina/San_Juan",
                        "America/Argentina/San_Juan",
                    ),
                    (
                        "America/Argentina/San_Luis",
                        "America/Argentina/San_Luis",
                    ),
                    ("Australia/LHI", "Australia/LHI"),
                    ("Europe/Tiraspol", "Europe/Tiraspol"),
                    ("Africa/Maputo", "Africa/Maputo"),
                    ("Europe/Kaliningrad", "Europe/Kaliningrad"),
                    ("Indian/Mahe", "Indian/Mahe"),
                    ("Africa/Niamey", "Africa/Niamey"),
                    ("Asia/Kuching", "Asia/Kuching"),
                    ("Pacific/Guam", "Pacific/Guam"),
                    ("Asia/Baku", "Asia/Baku"),
                    ("US/Eastern", "US/Eastern"),
                    ("America/Toronto", "America/Toronto"),
                    ("Africa/Malabo", "Africa/Malabo"),
                    ("Etc/GMT+0", "Etc/GMT+0"),
                    ("America/El_Salvador", "America/El_Salvador"),
                    ("Etc/GMT-2", "Etc/GMT-2"),
                    ("Pacific/Galapagos", "Pacific/Galapagos"),
                    ("Asia/Katmandu", "Asia/Katmandu"),
                    ("America/Boa_Vista", "America/Boa_Vista"),
                    ("Africa/Freetown", "Africa/Freetown"),
                    ("Europe/London", "Europe/London"),
                    ("Australia/ACT", "Australia/ACT"),
                    ("America/Virgin", "America/Virgin"),
                    ("Pacific/Rarotonga", "Pacific/Rarotonga"),
                    ("America/Mendoza", "America/Mendoza"),
                    ("America/Regina", "America/Regina"),
                    ("Asia/Makassar", "Asia/Makassar"),
                    ("Pacific/Tongatapu", "Pacific/Tongatapu"),
                    ("Africa/Djibouti", "Africa/Djibouti"),
                    ("Asia/Nicosia", "Asia/Nicosia"),
                    ("America/Argentina/Salta", "America/Argentina/Salta"),
                    ("Asia/Istanbul", "Asia/Istanbul"),
                    ("Etc/GMT-4", "Etc/GMT-4"),
                    ("GB", "GB"),
                    ("Etc/GMT+10", "Etc/GMT+10"),
                    ("America/Halifax", "America/Halifax"),
                    ("America/Santo_Domingo", "America/Santo_Domingo"),
                    ("Asia/Oral", "Asia/Oral"),
                    ("ROK", "ROK"),
                    ("America/Curacao", "America/Curacao"),
                    ("Europe/Berlin", "Europe/Berlin"),
                    ("Australia/Victoria", "Australia/Victoria"),
                    ("Navajo", "Navajo"),
                    ("Asia/Pontianak", "Asia/Pontianak"),
                    ("Europe/Zurich", "Europe/Zurich"),
                    ("Etc/UCT", "Etc/UCT"),
                    ("America/Chicago", "America/Chicago"),
                    ("America/Jujuy", "America/Jujuy"),
                    ("America/Atikokan", "America/Atikokan"),
                    ("America/Adak", "America/Adak"),
                    ("Europe/Tallinn", "Europe/Tallinn"),
                    ("Antarctica/Rothera", "Antarctica/Rothera"),
                    ("Indian/Christmas", "Indian/Christmas"),
                    ("Africa/Algiers", "Africa/Algiers"),
                    ("America/St_Thomas", "America/St_Thomas"),
                    ("Iceland", "Iceland"),
                    ("Pacific/Pohnpei", "Pacific/Pohnpei"),
                    ("America/Whitehorse", "America/Whitehorse"),
                    ("Asia/Ho_Chi_Minh", "Asia/Ho_Chi_Minh"),
                    ("Cuba", "Cuba"),
                    ("Pacific/Tarawa", "Pacific/Tarawa"),
                    ("Pacific/Niue", "Pacific/Niue"),
                    ("America/Bahia", "America/Bahia"),
                    ("America/St_Johns", "America/St_Johns"),
                    ("America/St_Vincent", "America/St_Vincent"),
                    ("Europe/Ulyanovsk", "Europe/Ulyanovsk"),
                    ("Asia/Yekaterinburg", "Asia/Yekaterinburg"),
                    ("Canada/Central", "Canada/Central"),
                    ("Asia/Taipei", "Asia/Taipei"),
                    ("Africa/Bamako", "Africa/Bamako"),
                    ("Europe/Amsterdam", "Europe/Amsterdam"),
                    ("Etc/GMT-5", "Etc/GMT-5"),
                    ("Antarctica/Palmer", "Antarctica/Palmer"),
                    ("Pacific/Honolulu", "Pacific/Honolulu"),
                    ("Brazil/East", "Brazil/East"),
                    ("America/Indiana/Vevay", "America/Indiana/Vevay"),
                    ("Europe/Mariehamn", "Europe/Mariehamn"),
                    ("Asia/Chungking", "Asia/Chungking"),
                    ("Europe/Samara", "Europe/Samara"),
                    ("Asia/Kamchatka", "Asia/Kamchatka"),
                    ("America/Argentina/Tucuman", "America/Argentina/Tucuman"),
                    ("Canada/Atlantic", "Canada/Atlantic"),
                    ("America/Argentina/Cordoba", "America/Argentina/Cordoba"),
                    ("Etc/GMT-1", "Etc/GMT-1"),
                    ("Etc/GMT+12", "Etc/GMT+12"),
                    ("America/Boise", "America/Boise"),
                    ("America/Swift_Current", "America/Swift_Current"),
                    ("Africa/Lome", "Africa/Lome"),
                    ("Asia/Pyongyang", "Asia/Pyongyang"),
                    ("Asia/Bahrain", "Asia/Bahrain"),
                    ("America/Grand_Turk", "America/Grand_Turk"),
                    ("Africa/Tunis", "Africa/Tunis"),
                    ("America/Barbados", "America/Barbados"),
                    ("Europe/Kyiv", "Europe/Kyiv"),
                    ("Asia/Harbin", "Asia/Harbin"),
                    ("Etc/GMT-9", "Etc/GMT-9"),
                    ("Pacific/Enderbury", "Pacific/Enderbury"),
                    ("PRC", "PRC"),
                    ("Etc/GMT+3", "Etc/GMT+3"),
                    ("America/Shiprock", "America/Shiprock"),
                    ("America/Juneau", "America/Juneau"),
                    ("Australia/Queensland", "Australia/Queensland"),
                    ("Africa/Monrovia", "Africa/Monrovia"),
                    ("America/Martinique", "America/Martinique"),
                    ("Etc/GMT-10", "Etc/GMT-10"),
                    ("PST8PDT", "PST8PDT"),
                    ("America/Rio_Branco", "America/Rio_Branco"),
                    ("Pacific/Palau", "Pacific/Palau"),
                    ("Asia/Novosibirsk", "Asia/Novosibirsk"),
                    ("America/Managua", "America/Managua"),
                    ("MET", "MET"),
                    ("Asia/Anadyr", "Asia/Anadyr"),
                    ("CST6CDT", "CST6CDT"),
                    ("Brazil/West", "Brazil/West"),
                    ("America/Dawson", "America/Dawson"),
                    ("Asia/Kabul", "Asia/Kabul"),
                    ("Africa/Conakry", "Africa/Conakry"),
                    ("America/Tegucigalpa", "America/Tegucigalpa"),
                    ("Asia/Famagusta", "Asia/Famagusta"),
                    ("Etc/GMT-3", "Etc/GMT-3"),
                    ("Africa/Brazzaville", "Africa/Brazzaville"),
                    ("America/Porto_Acre", "America/Porto_Acre"),
                    ("US/East-Indiana", "US/East-Indiana"),
                    ("America/Guatemala", "America/Guatemala"),
                    ("Atlantic/Jan_Mayen", "Atlantic/Jan_Mayen"),
                    ("Chile/EasterIsland", "Chile/EasterIsland"),
                    ("Etc/GMT", "Etc/GMT"),
                    ("Asia/Samarkand", "Asia/Samarkand"),
                    ("Canada/Pacific", "Canada/Pacific"),
                    ("GMT+0", "GMT+0"),
                    ("America/Aruba", "America/Aruba"),
                    ("Pacific/Bougainville", "Pacific/Bougainville"),
                    ("Asia/Vientiane", "Asia/Vientiane"),
                    ("Africa/Blantyre", "Africa/Blantyre"),
                    ("Asia/Riyadh", "Asia/Riyadh"),
                    ("Africa/Maseru", "Africa/Maseru"),
                    ("Asia/Ujung_Pandang", "Asia/Ujung_Pandang"),
                    ("Asia/Beirut", "Asia/Beirut"),
                    ("Etc/GMT+4", "Etc/GMT+4"),
                    ("America/Jamaica", "America/Jamaica"),
                    ("America/Detroit", "America/Detroit"),
                    ("Australia/South", "Australia/South"),
                    ("Canada/Saskatchewan", "Canada/Saskatchewan"),
                    ("America/Antigua", "America/Antigua"),
                    ("America/Ciudad_Juarez", "America/Ciudad_Juarez"),
                    ("Antarctica/Vostok", "Antarctica/Vostok"),
                    ("Pacific/Chuuk", "Pacific/Chuuk"),
                    (
                        "America/Argentina/ComodRivadavia",
                        "America/Argentina/ComodRivadavia",
                    ),
                    ("Australia/Tasmania", "Australia/Tasmania"),
                    ("Australia/Sydney", "Australia/Sydney"),
                    ("US/Indiana-Starke", "US/Indiana-Starke"),
                    ("America/Araguaina", "America/Araguaina"),
                    ("Atlantic/Azores", "Atlantic/Azores"),
                    ("America/Cordoba", "America/Cordoba"),
                    ("Asia/Phnom_Penh", "Asia/Phnom_Penh"),
                    ("Turkey", "Turkey"),
                    ("America/Danmarkshavn", "America/Danmarkshavn"),
                    ("HST", "HST"),
                    ("Asia/Sakhalin", "Asia/Sakhalin"),
                    ("America/Catamarca", "America/Catamarca"),
                    ("America/Creston", "America/Creston"),
                    ("Asia/Kathmandu", "Asia/Kathmandu"),
                    ("America/Los_Angeles", "America/Los_Angeles"),
                    ("Pacific/Guadalcanal", "Pacific/Guadalcanal"),
                    ("America/Denver", "America/Denver"),
                    ("US/Hawaii", "US/Hawaii"),
                    ("NZ-CHAT", "NZ-CHAT"),
                    ("GMT-0", "GMT-0"),
                    ("Asia/Hovd", "Asia/Hovd"),
                    ("America/Yakutat", "America/Yakutat"),
                    ("Europe/Zagreb", "Europe/Zagreb"),
                    ("America/Dawson_Creek", "America/Dawson_Creek"),
                    ("Asia/Colombo", "Asia/Colombo"),
                    ("Jamaica", "Jamaica"),
                    ("Pacific/Yap", "Pacific/Yap"),
                    (
                        "America/North_Dakota/Beulah",
                        "America/North_Dakota/Beulah",
                    ),
                    ("Europe/Jersey", "Europe/Jersey"),
                    ("Australia/NSW", "Australia/NSW"),
                    ("GB-Eire", "GB-Eire"),
                    ("Atlantic/Faroe", "Atlantic/Faroe"),
                    ("America/Fort_Nelson", "America/Fort_Nelson"),
                    ("Antarctica/Davis", "Antarctica/Davis"),
                    ("Australia/Hobart", "Australia/Hobart"),
                    ("Africa/Kigali", "Africa/Kigali"),
                    ("Europe/Warsaw", "Europe/Warsaw"),
                    ("America/Argentina/Jujuy", "America/Argentina/Jujuy"),
                    ("America/Fort_Wayne", "America/Fort_Wayne"),
                    ("Europe/Monaco", "Europe/Monaco"),
                    ("Asia/Calcutta", "Asia/Calcutta"),
                    ("America/Atka", "America/Atka"),
                    ("MST7MDT", "MST7MDT"),
                    ("Asia/Almaty", "Asia/Almaty"),
                    ("Brazil/DeNoronha", "Brazil/DeNoronha"),
                    ("Australia/North", "Australia/North"),
                    ("Universal", "Universal"),
                    ("Etc/GMT-13", "Etc/GMT-13"),
                    ("Africa/Libreville", "Africa/Libreville"),
                    ("Africa/Luanda", "Africa/Luanda"),
                    ("America/Coyhaique", "America/Coyhaique"),
                    ("America/Cambridge_Bay", "America/Cambridge_Bay"),
                    ("Pacific/Pago_Pago", "Pacific/Pago_Pago"),
                    (
                        "America/Argentina/Buenos_Aires",
                        "America/Argentina/Buenos_Aires",
                    ),
                    ("Asia/Seoul", "Asia/Seoul"),
                    ("Antarctica/Macquarie", "Antarctica/Macquarie"),
                    ("Europe/Vatican", "Europe/Vatican"),
                    ("Asia/Yerevan", "Asia/Yerevan"),
                    ("America/Knox_IN", "America/Knox_IN"),
                    ("America/Port_of_Spain", "America/Port_of_Spain"),
                    ("Asia/Dacca", "Asia/Dacca"),
                    ("America/Mazatlan", "America/Mazatlan"),
                    ("Europe/Sarajevo", "Europe/Sarajevo"),
                    ("Atlantic/Madeira", "Atlantic/Madeira"),
                    ("Australia/West", "Australia/West"),
                    ("Europe/Bucharest", "Europe/Bucharest"),
                    ("Africa/El_Aaiun", "Africa/El_Aaiun"),
                    ("Europe/Copenhagen", "Europe/Copenhagen"),
                    ("Europe/Volgograd", "Europe/Volgograd"),
                    ("Australia/Perth", "Australia/Perth"),
                    ("Europe/Vienna", "Europe/Vienna"),
                    ("America/Indianapolis", "America/Indianapolis"),
                    ("America/Hermosillo", "America/Hermosillo"),
                    ("Pacific/Apia", "Pacific/Apia"),
                    (
                        "America/Argentina/La_Rioja",
                        "America/Argentina/La_Rioja",
                    ),
                    ("Asia/Tomsk", "Asia/Tomsk"),
                    ("Etc/GMT+9", "Etc/GMT+9"),
                    ("Antarctica/Troll", "Antarctica/Troll"),
                    ("America/Pangnirtung", "America/Pangnirtung"),
                    ("Europe/Paris", "Europe/Paris"),
                    ("America/Havana", "America/Havana"),
                    ("Africa/Asmera", "Africa/Asmera"),
                    ("Pacific/Fiji", "Pacific/Fiji"),
                    ("Asia/Aden", "Asia/Aden"),
                    ("Pacific/Marquesas", "Pacific/Marquesas"),
                    ("Africa/Lagos", "Africa/Lagos"),
                    ("Africa/Kinshasa", "Africa/Kinshasa"),
                    ("America/Goose_Bay", "America/Goose_Bay"),
                    ("Etc/GMT+2", "Etc/GMT+2"),
                    ("America/Phoenix", "America/Phoenix"),
                    ("Asia/Kashgar", "Asia/Kashgar"),
                    ("America/Mexico_City", "America/Mexico_City"),
                    ("Australia/Eucla", "Australia/Eucla"),
                    ("Africa/Addis_Ababa", "Africa/Addis_Ababa"),
                    ("Etc/GMT-14", "Etc/GMT-14"),
                    ("Etc/GMT+6", "Etc/GMT+6"),
                    ("Canada/Mountain", "Canada/Mountain"),
                    ("America/Metlakatla", "America/Metlakatla"),
                    ("Pacific/Wake", "Pacific/Wake"),
                    ("Indian/Antananarivo", "Indian/Antananarivo"),
                    ("W-SU", "W-SU"),
                    ("America/Santa_Isabel", "America/Santa_Isabel"),
                    ("Europe/Vaduz", "Europe/Vaduz"),
                    ("Europe/Minsk", "Europe/Minsk"),
                    ("Africa/Johannesburg", "Africa/Johannesburg"),
                    ("Pacific/Easter", "Pacific/Easter"),
                    ("America/Ensenada", "America/Ensenada"),
                    ("America/Porto_Velho", "America/Porto_Velho"),
                    ("Asia/Thimbu", "Asia/Thimbu"),
                    ("Africa/Porto-Novo", "Africa/Porto-Novo"),
                    ("Australia/Broken_Hill", "Australia/Broken_Hill"),
                    ("America/St_Lucia", "America/St_Lucia"),
                    ("America/Manaus", "America/Manaus"),
                    ("America/Tijuana", "America/Tijuana"),
                    ("America/Louisville", "America/Louisville"),
                    ("America/Campo_Grande", "America/Campo_Grande"),
                    ("Asia/Singapore", "Asia/Singapore"),
                    ("America/Moncton", "America/Moncton"),
                    ("Asia/Urumqi", "Asia/Urumqi"),
                    ("Indian/Mayotte", "Indian/Mayotte"),
                    ("Atlantic/Faeroe", "Atlantic/Faeroe"),
                    ("Africa/Windhoek", "Africa/Windhoek"),
                    ("America/Recife", "America/Recife"),
                    ("US/Mountain", "US/Mountain"),
                    ("Australia/Currie", "Australia/Currie"),
                    ("localtime", "localtime"),
                    ("America/Guayaquil", "America/Guayaquil"),
                    ("America/Monterrey", "America/Monterrey"),
                    ("Asia/Chita", "Asia/Chita"),
                    ("Asia/Irkutsk", "Asia/Irkutsk"),
                    ("Etc/UTC", "Etc/UTC"),
                    ("America/Anchorage", "America/Anchorage"),
                    ("Asia/Ulaanbaatar", "Asia/Ulaanbaatar"),
                    ("Atlantic/Stanley", "Atlantic/Stanley"),
                    ("America/Glace_Bay", "America/Glace_Bay"),
                    ("America/Cancun", "America/Cancun"),
                    ("Mexico/General", "Mexico/General"),
                    ("America/Tortola", "America/Tortola"),
                    ("America/Rosario", "America/Rosario"),
                    ("America/Indiana/Marengo", "America/Indiana/Marengo"),
                    ("Singapore", "Singapore"),
                    ("Asia/Qyzylorda", "Asia/Qyzylorda"),
                    ("Africa/Lubumbashi", "Africa/Lubumbashi"),
                    ("Asia/Ashgabat", "Asia/Ashgabat"),
                    ("Asia/Thimphu", "Asia/Thimphu"),
                    ("Asia/Saigon", "Asia/Saigon"),
                    ("Asia/Shanghai", "Asia/Shanghai"),
                    ("Africa/Ndjamena", "Africa/Ndjamena"),
                    ("Asia/Hong_Kong", "Asia/Hong_Kong"),
                    ("Asia/Tehran", "Asia/Tehran"),
                    ("Atlantic/South_Georgia", "Atlantic/South_Georgia"),
                    ("Factory", "Factory"),
                    ("Africa/Mbabane", "Africa/Mbabane"),
                    ("America/Marigot", "America/Marigot"),
                    ("Etc/GMT+5", "Etc/GMT+5"),
                    ("Etc/Greenwich", "Etc/Greenwich"),
                    ("Pacific/Majuro", "Pacific/Majuro"),
                    ("America/Lower_Princes", "America/Lower_Princes"),
                    ("Asia/Barnaul", "Asia/Barnaul"),
                    ("Indian/Mauritius", "Indian/Mauritius"),
                    ("Asia/Jayapura", "Asia/Jayapura"),
                    ("Pacific/Port_Moresby", "Pacific/Port_Moresby"),
                    ("GMT0", "GMT0"),
                    ("NZ", "NZ"),
                    ("Australia/Lord_Howe", "Australia/Lord_Howe"),
                    ("America/Indiana/Knox", "America/Indiana/Knox"),
                    ("America/Guadeloupe", "America/Guadeloupe"),
                    ("Europe/Helsinki", "Europe/Helsinki"),
                    ("America/Indiana/Vincennes", "America/Indiana/Vincennes"),
                    ("Europe/Ljubljana", "Europe/Ljubljana"),
                    ("Asia/Qatar", "Asia/Qatar"),
                    ("Europe/Kirov", "Europe/Kirov"),
                    ("Canada/Eastern", "Canada/Eastern"),
                    ("Pacific/Truk", "Pacific/Truk"),
                    ("America/Cayenne", "America/Cayenne"),
                    ("Pacific/Midway", "Pacific/Midway"),
                    ("Pacific/Kwajalein", "Pacific/Kwajalein"),
                    ("America/Nome", "America/Nome"),
                    ("America/Resolute", "America/Resolute"),
                    ("America/Rainy_River", "America/Rainy_River"),
                    ("Europe/Andorra", "Europe/Andorra"),
                    ("Asia/Tokyo", "Asia/Tokyo"),
                    ("Pacific/Wallis", "Pacific/Wallis"),
                    ("Japan", "Japan"),
                    ("America/Montreal", "America/Montreal"),
                    ("Pacific/Efate", "Pacific/Efate"),
                    ("Europe/Prague", "Europe/Prague"),
                    ("America/Ojinaga", "America/Ojinaga"),
                    ("Indian/Kerguelen", "Indian/Kerguelen"),
                    ("Europe/Gibraltar", "Europe/Gibraltar"),
                    ("Pacific/Saipan", "Pacific/Saipan"),
                    ("CET", "CET"),
                    ("Etc/GMT-11", "Etc/GMT-11"),
                    ("Asia/Srednekolymsk", "Asia/Srednekolymsk"),
                    ("Europe/Kiev", "Europe/Kiev"),
                    ("US/Samoa", "US/Samoa"),
                    ("Asia/Krasnoyarsk", "Asia/Krasnoyarsk"),
                    ("Asia/Brunei", "Asia/Brunei"),
                    ("Europe/Madrid", "Europe/Madrid"),
                    ("Europe/Saratov", "Europe/Saratov"),
                    ("Australia/Melbourne", "Australia/Melbourne"),
                    ("Asia/Dili", "Asia/Dili"),
                    (
                        "America/North_Dakota/New_Salem",
                        "America/North_Dakota/New_Salem",
                    ),
                    ("Australia/Brisbane", "Australia/Brisbane"),
                    ("WET", "WET"),
                    ("America/Winnipeg", "America/Winnipeg"),
                    ("America/Kralendijk", "America/Kralendijk"),
                    (
                        "America/Argentina/Rio_Gallegos",
                        "America/Argentina/Rio_Gallegos",
                    ),
                    ("America/Thule", "America/Thule"),
                    ("Africa/Bujumbura", "Africa/Bujumbura"),
                    ("Asia/Bangkok", "Asia/Bangkok"),
                    ("Pacific/Kanton", "Pacific/Kanton"),
                    ("Africa/Bissau", "Africa/Bissau"),
                    ("Asia/Bishkek", "Asia/Bishkek"),
                    ("Africa/Casablanca", "Africa/Casablanca"),
                    ("Etc/GMT0", "Etc/GMT0"),
                    ("America/Nassau", "America/Nassau"),
                    ("Pacific/Gambier", "Pacific/Gambier"),
                    ("America/St_Kitts", "America/St_Kitts"),
                    ("Antarctica/Mawson", "Antarctica/Mawson"),
                    ("Asia/Tel_Aviv", "Asia/Tel_Aviv"),
                    ("Israel", "Israel"),
                    ("America/Maceio", "America/Maceio"),
                    ("America/Blanc-Sablon", "America/Blanc-Sablon"),
                    ("America/Bahia_Banderas", "America/Bahia_Banderas"),
                    ("America/Punta_Arenas", "America/Punta_Arenas"),
                    ("America/Scoresbysund", "America/Scoresbysund"),
                    ("America/Montevideo", "America/Montevideo"),
                    ("America/Sitka", "America/Sitka"),
                    ("Africa/Juba", "Africa/Juba"),
                    ("America/Anguilla", "America/Anguilla"),
                    ("Australia/Yancowinna", "Australia/Yancowinna"),
                    ("Asia/Amman", "Asia/Amman"),
                    ("Europe/San_Marino", "Europe/San_Marino"),
                    ("Etc/Universal", "Etc/Universal"),
                    ("America/Bogota", "America/Bogota"),
                    ("Asia/Baghdad", "Asia/Baghdad"),
                    ("America/Rankin_Inlet", "America/Rankin_Inlet"),
                    ("Mexico/BajaNorte", "Mexico/BajaNorte"),
                    ("America/La_Paz", "America/La_Paz"),
                    ("Asia/Aqtau", "Asia/Aqtau"),
                    (
                        "America/North_Dakota/Center",
                        "America/North_Dakota/Center",
                    ),
                    (
                        "America/Kentucky/Louisville",
                        "America/Kentucky/Louisville",
                    ),
                    ("US/Aleutian", "US/Aleutian"),
                    ("Africa/Kampala", "Africa/Kampala"),
                    ("Africa/Asmara", "Africa/Asmara"),
                    ("Africa/Mogadishu", "Africa/Mogadishu"),
                    ("America/Eirunepe", "America/Eirunepe"),
                    ("Etc/GMT-6", "Etc/GMT-6"),
                    ("Europe/Busingen", "Europe/Busingen"),
                    ("Asia/Kuwait", "Asia/Kuwait"),
                    ("Australia/Darwin", "Australia/Darwin"),
                    ("Europe/Vilnius", "Europe/Vilnius"),
                    ("America/Merida", "America/Merida"),
                    ("Australia/Lindeman", "Australia/Lindeman"),
                    ("Africa/Bangui", "Africa/Bangui"),
                    ("Asia/Chongqing", "Asia/Chongqing"),
                    ("America/Godthab", "America/Godthab"),
                    ("Atlantic/Cape_Verde", "Atlantic/Cape_Verde"),
                    ("Europe/Istanbul", "Europe/Istanbul"),
                    ("America/Buenos_Aires", "America/Buenos_Aires"),
                    ("Asia/Khandyga", "Asia/Khandyga"),
                    ("Asia/Macau", "Asia/Macau"),
                    ("Europe/Riga", "Europe/Riga"),
                    ("Antarctica/McMurdo", "Antarctica/McMurdo"),
                    ("Africa/Cairo", "Africa/Cairo"),
                    (
                        "America/Indiana/Petersburg",
                        "America/Indiana/Petersburg",
                    ),
                    ("EST5EDT", "EST5EDT"),
                    ("Antarctica/Syowa", "Antarctica/Syowa"),
                    ("Pacific/Auckland", "Pacific/Auckland"),
                    (
                        "America/Argentina/Catamarca",
                        "America/Argentina/Catamarca",
                    ),
                    ("Asia/Ust-Nera", "Asia/Ust-Nera"),
                    ("Asia/Dhaka", "Asia/Dhaka"),
                    ("Atlantic/Bermuda", "Atlantic/Bermuda"),
                    ("Brazil/Acre", "Brazil/Acre"),
                    ("Pacific/Noumea", "Pacific/Noumea"),
                    ("Eire", "Eire"),
                    ("Asia/Magadan", "Asia/Magadan"),
                    ("America/Matamoros", "America/Matamoros"),
                    ("Indian/Cocos", "Indian/Cocos"),
                    ("America/Santiago", "America/Santiago"),
                    ("America/Vancouver", "America/Vancouver"),
                    ("Indian/Comoro", "Indian/Comoro"),
                    ("Europe/Zaporozhye", "Europe/Zaporozhye"),
                    ("Australia/Adelaide", "Australia/Adelaide"),
                    ("Africa/Banjul", "Africa/Banjul"),
                    ("Portugal", "Portugal"),
                    ("Zulu", "Zulu"),
                    ("America/Belem", "America/Belem"),
                    ("Africa/Nairobi", "Africa/Nairobi"),
                    ("Canada/Yukon", "Canada/Yukon"),
                    ("America/Indiana/Winamac", "America/Indiana/Winamac"),
                    ("America/Caracas", "America/Caracas"),
                    ("Africa/Ceuta", "Africa/Ceuta"),
                    ("Iran", "Iran"),
                    ("Asia/Muscat", "Asia/Muscat"),
                    ("Etc/GMT-8", "Etc/GMT-8"),
                    ("Asia/Gaza", "Asia/Gaza"),
                    ("Pacific/Funafuti", "Pacific/Funafuti"),
                    ("Europe/Moscow", "Europe/Moscow"),
                    ("America/Coral_Harbour", "America/Coral_Harbour"),
                    ("Asia/Novokuznetsk", "Asia/Novokuznetsk"),
                    ("Asia/Jerusalem", "Asia/Jerusalem"),
                    ("Europe/Budapest", "Europe/Budapest"),
                    ("Etc/GMT+1", "Etc/GMT+1"),
                    ("Asia/Kuala_Lumpur", "Asia/Kuala_Lumpur"),
                    ("America/Menominee", "America/Menominee"),
                    ("Asia/Damascus", "Asia/Damascus"),
                    ("Pacific/Nauru", "Pacific/Nauru"),
                    ("America/St_Barthelemy", "America/St_Barthelemy"),
                    ("Europe/Uzhgorod", "Europe/Uzhgorod"),
                    ("Europe/Astrakhan", "Europe/Astrakhan"),
                    ("Europe/Luxembourg", "Europe/Luxembourg"),
                    ("Asia/Kolkata", "Asia/Kolkata"),
                    ("Asia/Qostanay", "Asia/Qostanay"),
                    ("Greenwich", "Greenwich"),
                    ("America/Chihuahua", "America/Chihuahua"),
                    ("Atlantic/Canary", "Atlantic/Canary"),
                    ("Canada/Newfoundland", "Canada/Newfoundland"),
                    ("Europe/Athens", "Europe/Athens"),
                    ("ROC", "ROC"),
                    ("Europe/Nicosia", "Europe/Nicosia"),
                    ("Asia/Manila", "Asia/Manila"),
                    ("Asia/Omsk", "Asia/Omsk"),
                    ("America/Nuuk", "America/Nuuk"),
                    ("Pacific/Kosrae", "Pacific/Kosrae"),
                    ("Mexico/BajaSur", "Mexico/BajaSur"),
                    ("Atlantic/Reykjavik", "Atlantic/Reykjavik"),
                    ("Etc/GMT-7", "Etc/GMT-7"),
                    ("Europe/Rome", "Europe/Rome"),
                    ("Kwajalein", "Kwajalein"),
                    ("America/New_York", "America/New_York"),
                    ("US/Alaska", "US/Alaska"),
                    ("Asia/Ashkhabad", "Asia/Ashkhabad"),
                    ("Europe/Belgrade", "Europe/Belgrade"),
                    ("Europe/Podgorica", "Europe/Podgorica"),
                    ("Libya", "Libya"),
                    ("Egypt", "Egypt"),
                    ("EET", "EET"),
                    ("Asia/Hebron", "Asia/Hebron"),
                    ("Etc/GMT+7", "Etc/GMT+7"),
                    ("Europe/Sofia", "Europe/Sofia"),
                    ("Europe/Stockholm", "Europe/Stockholm"),
                    ("America/Miquelon", "America/Miquelon"),
                    ("Australia/Canberra", "Australia/Canberra"),
                    ("US/Michigan", "US/Michigan"),
                    ("Pacific/Ponape", "Pacific/Ponape"),
                    ("Etc/GMT+8", "Etc/GMT+8"),
                    ("America/Argentina/Mendoza", "America/Argentina/Mendoza"),
                    ("Pacific/Norfolk", "Pacific/Norfolk"),
                    ("Africa/Abidjan", "Africa/Abidjan"),
                    ("Asia/Atyrau", "Asia/Atyrau"),
                    ("America/Grenada", "America/Grenada"),
                    ("America/Sao_Paulo", "America/Sao_Paulo"),
                    ("Pacific/Tahiti", "Pacific/Tahiti"),
                    (
                        "America/Indiana/Indianapolis",
                        "America/Indiana/Indianapolis",
                    ),
                    ("Asia/Yangon", "Asia/Yangon"),
                    ("America/Argentina/Ushuaia", "America/Argentina/Ushuaia"),
                    ("America/Montserrat", "America/Montserrat"),
                    ("US/Arizona", "US/Arizona"),
                    ("Asia/Yakutsk", "Asia/Yakutsk"),
                    ("Pacific/Johnston", "Pacific/Johnston"),
                    ("Africa/Gaborone", "Africa/Gaborone"),
                    ("America/Guyana", "America/Guyana"),
                    ("US/Pacific", "US/Pacific"),
                    ("MST", "MST"),
                    ("America/Asuncion", "America/Asuncion"),
                    ("Asia/Karachi", "Asia/Karachi"),
                    ("America/Paramaribo", "America/Paramaribo"),
                    ("Arctic/Longyearbyen", "Arctic/Longyearbyen"),
                    ("Europe/Chisinau", "Europe/Chisinau"),
                    ("Asia/Aqtobe", "Asia/Aqtobe"),
                    ("Europe/Lisbon", "Europe/Lisbon"),
                    ("Indian/Reunion", "Indian/Reunion"),
                    ("America/Nipigon", "America/Nipigon"),
                    (
                        "America/Kentucky/Monticello",
                        "America/Kentucky/Monticello",
                    ),
                    ("America/Inuvik", "America/Inuvik"),
                    ("Poland", "Poland"),
                    ("America/Dominica", "America/Dominica"),
                    ("America/Costa_Rica", "America/Costa_Rica"),
                    ("America/Cuiaba", "America/Cuiaba"),
                    ("America/Port-au-Prince", "America/Port-au-Prince"),
                    ("America/Cayman", "America/Cayman"),
                    ("Africa/Timbuktu", "Africa/Timbuktu"),
                    ("Africa/Lusaka", "Africa/Lusaka"),
                    ("America/Santarem", "America/Santarem"),
                    ("Asia/Macao", "Asia/Macao"),
                    ("Europe/Skopje", "Europe/Skopje"),
                    ("Asia/Rangoon", "Asia/Rangoon"),
                    ("America/Indiana/Tell_City", "America/Indiana/Tell_City"),
                    ("America/Puerto_Rico", "America/Puerto_Rico"),
                    ("Indian/Chagos", "Indian/Chagos"),
                    ("GMT", "GMT"),
                    ("Pacific/Kiritimati", "Pacific/Kiritimati"),
                    ("Africa/Douala", "Africa/Douala"),
                    ("Hongkong", "Hongkong"),
                    ("Asia/Choibalsan", "Asia/Choibalsan"),
                    ("Africa/Harare", "Africa/Harare"),
                ],
                default="UTC",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="enterprise",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="trip",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True
            ),
        ),
    ]
