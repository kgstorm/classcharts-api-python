# classcharts-api

A Python port of [classcharts-api-js](https://github.com/classchartsapi/classcharts-api-js) by James Cook.

Provides an async Python client for the ClassCharts parent and student APIs.

## Installation

```bash
pip install classcharts-api
```

## Usage

```python
import asyncio
from classcharts_api import ParentClient

async def main():
    async with ParentClient("email@example.com", "password") as client:
        await client.login()
        pupils = client.pupils
        homeworks = await client.get_homeworks_for_each_pupil(
            display_date="due_date",
            from_date="2026-01-01",
            to_date="2026-07-01",
        )
        for pupil_id, resp in homeworks.items():
            print(f"Pupil {pupil_id}: {len(resp['data'])} homework items")

asyncio.run(main())
```

## License

ISC License — see [LICENSE](LICENSE).

This project is a Python port of [classcharts-api-js](https://github.com/classchartsapi/classcharts-api-js), copyright (c) 2022 James Cook, used under the ISC License.
